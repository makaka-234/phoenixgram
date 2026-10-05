"""Менеджер WebSocket-соединений.

Локальные соединения хранятся в памяти процесса. Доставка между узлами —
через Redis pub/sub (канал user:{id}). Это позволяет запускать несколько
реплик backend и всё равно доставлять сообщения.
"""
from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Dict, Iterable, Set

from fastapi import WebSocket

from app.core.redis_client import publish, subscribe

logger = logging.getLogger("phoenixgram.ws")

USER_CHANNEL = "user:{user_id}"
CHANNEL_PATTERN = "user:*"


class ConnectionManager:
    def __init__(self) -> None:
        self._local: Dict[int, Set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()
        self._consumer_task: asyncio.Task | None = None

    # ---------- локальные соединения ----------
    async def connect(self, user_id: int, ws: WebSocket) -> None:
        async with self._lock:
            self._local[user_id].add(ws)
        logger.debug("WS подключён: user=%s (всего %s)", user_id, len(self._local[user_id]))

    async def disconnect(self, user_id: int, ws: WebSocket) -> None:
        async with self._lock:
            conns = self._local.get(user_id)
            if conns:
                conns.discard(ws)
                if not conns:
                    self._local.pop(user_id, None)
        logger.debug("WS отключён: user=%s", user_id)

    def is_online(self, user_id: int) -> bool:
        return bool(self._local.get(user_id))

    def online_user_ids(self) -> list[int]:
        return list(self._local.keys())

    async def send_local(self, user_id: int, payload: dict) -> None:
        conns = list(self._local.get(user_id, ()))
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(user_id, ws)

    # ---------- доставка ----------
    async def emit(self, user_ids: Iterable[int], payload: dict) -> None:
        """Опубликовать событие в Redis — его получат все узлы."""
        for uid in set(user_ids):
            await publish(USER_CHANNEL.format(user_id=uid), payload)

    async def emit_local(self, user_ids: Iterable[int], payload: dict) -> None:
        for uid in set(user_ids):
            await self.send_local(uid, payload)

    # ---------- фоновый потребитель ----------
    async def _consume(self) -> None:
        logger.info("WS consumer запущен (pattern=%s)", CHANNEL_PATTERN)
        try:
            async for event in subscribe(CHANNEL_PATTERN):
                payload: Any = event.get("payload")
                # Ключ канала не нужен: получатели уже в payload.
                for uid in event.get("to", []):
                    await self.send_local(int(uid), payload)
        except asyncio.CancelledError:  # pragma: no cover
            logger.info("WS consumer остановлен")
            raise
        except Exception:  # pragma: no cover
            logger.exception("WS consumer упал")

    def start_consumer(self) -> None:
        if self._consumer_task is None or self._consumer_task.done():
            self._consumer_task = asyncio.create_task(self._consume())

    async def stop_consumer(self) -> None:
        if self._consumer_task is not None:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            self._consumer_task = None


manager = ConnectionManager()


async def push_to_users(user_ids: Iterable[int], payload: dict) -> None:
    """Удобная обёртка: отправить событие пользователям на всех узлах.

    Публикуем в Redis (его получит и этот узел через consumer). Если Redis
    недоступен — не роняем основной сценарий (оплата, перевод), а доставляем
    хотя бы локально и пишем предупреждение.
    """
    ids = list(set(int(u) for u in user_ids))
    if not ids:
        return
    for uid in ids:
        try:
            await publish(
                USER_CHANNEL.format(user_id=uid),
                {"to": [uid], "payload": payload},
            )
        except Exception:
            logger.warning("Redis недоступен — доставляю событие локально (user=%s)", uid, exc_info=False)
            await manager.send_local(uid, payload)
