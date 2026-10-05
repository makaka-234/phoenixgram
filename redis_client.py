"""Redis: кэш, pub/sub для WebSocket."""
from __future__ import annotations

import json
from typing import Any, AsyncGenerator, Optional

import redis.asyncio as aioredis

from app.core.config import settings

redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            health_check_interval=30,
        )
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None


def get_redis() -> aioredis.Redis:
    if redis_client is None:
        raise RuntimeError("Redis не инициализирован. Вызовите init_redis().")
    return redis_client


# ---------------------- Кэш ----------------------


async def cache_set(key: str, value: Any, ttl: int = 60) -> None:
    r = get_redis()
    await r.set(key, json.dumps(value, ensure_ascii=False, default=str), ex=ttl)


async def cache_get(key: str) -> Any | None:
    r = get_redis()
    raw = await r.get(key)
    return json.loads(raw) if raw else None


async def cache_delete(*keys: str) -> None:
    r = get_redis()
    if keys:
        await r.delete(*keys)


# ---------------------- Pub/Sub ----------------------


async def publish(channel: str, payload: dict) -> None:
    """Опубликовать событие (например, для доставки WebSocket на любом узле)."""
    r = get_redis()
    await r.publish(channel, json.dumps(payload, ensure_ascii=False, default=str))


async def subscribe(channel_pattern: str) -> AsyncGenerator[dict, None]:
    """Подписаться на события по маске каналов (psubscribe)."""
    r = get_redis()
    pubsub = r.pubsub()
    await pubsub.psubscribe(channel_pattern)
    try:
        async for message in pubsub.listen():
            if message.get("type") != "pmessage":
                continue
            try:
                yield json.loads(message["data"])
            except (TypeError, json.JSONDecodeError):
                continue
    finally:
        await pubsub.punsubscribe(channel_pattern)
        await pubsub.aclose()
