"""WebSocket: real-time обмен сообщениями, набор текста, прочтение, presence."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.deps import require_ws_token
from app.models.user import User
from app.services import chat_service, message_service
from app.services.chat_service import ChatError
from app.services.message_service import MessageError
from app.ws.manager import manager, push_to_users
from app.ws.serialize import message_dict, user_short

logger = logging.getLogger("phoenixgram.ws")
router = APIRouter(tags=["WebSocket"])


async def _get_user(db, user_id: int) -> User | None:
    return await db.get(User, user_id)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(default="")):
    try:
        user_id = require_ws_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    async with AsyncSessionLocal() as db:
        user = await _get_user(db, user_id)
        if user is None or user.is_banned or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        user_ids = await _user_chat_ids(db, user_id)

    await manager.connect(user_id, websocket)

    # Сообщаем собеседникам, что пользователь онлайн.
    for chat_id in user_ids:
        async with AsyncSessionLocal() as db:
            members = await chat_service.member_user_ids(db, chat_id)
        await push_to_users(
            [m for m in members if m != user_id],
            {"event": "presence", "chat_id": chat_id, "payload": {"user_id": user_id, "online": True}},
        )

    try:
        while True:
            data = await websocket.receive_json()
            action = (data or {}).get("action")
            if action == "ping":
                await websocket.send_json({"event": "pong", "payload": {}})
            elif action == "typing":
                await _handle_typing(user_id, data)
            elif action == "read":
                await _handle_read(user_id, data)
            elif action == "send":
                await _handle_send(websocket, user_id, data)
            else:
                await websocket.send_json({"event": "error", "payload": {"detail": "Неизвестное действие"}})
    except WebSocketDisconnect:
        pass
    except Exception:  # pragma: no cover
        logger.exception("Ошибка WebSocket user=%s", user_id)
    finally:
        await manager.disconnect(user_id, websocket)
        for chat_id in user_ids:
            async with AsyncSessionLocal() as db:
                members = await chat_service.member_user_ids(db, chat_id)
            await push_to_users(
                [m for m in members if m != user_id],
                {"event": "presence", "chat_id": chat_id, "payload": {"user_id": user_id, "online": False}},
            )


async def _user_chat_ids(db, user_id: int) -> list[int]:
    from app.models.chat import ChatMember

    rows = (
        await db.execute(select(ChatMember.chat_id).where(ChatMember.user_id == user_id))
    ).scalars().all()
    return list(rows)


async def _handle_typing(user_id: int, data: dict) -> None:
    chat_id = data.get("chat_id")
    if not chat_id:
        return
    async with AsyncSessionLocal() as db:
        try:
            await chat_service.ensure_member(db, chat_id, user_id)
        except ChatError:
            return
        members = await chat_service.member_user_ids(db, chat_id)
    await push_to_users(
        [m for m in members if m != user_id],
        {"event": "typing", "chat_id": chat_id, "payload": {"user_id": user_id}},
    )


async def _handle_read(user_id: int, data: dict) -> None:
    chat_id = data.get("chat_id")
    payload = data.get("data") or {}
    message_id = payload.get("message_id")
    if not chat_id or message_id is None:
        return
    async with AsyncSessionLocal() as db:
        try:
            await chat_service.mark_read(db, chat_id, user_id, int(message_id))
        except ChatError:
            return
        members = await chat_service.member_user_ids(db, chat_id)
    await push_to_users(
        [m for m in members if m != user_id],
        {
            "event": "read",
            "chat_id": chat_id,
            "payload": {"user_id": user_id, "message_id": int(message_id)},
        },
    )


async def _handle_send(websocket: WebSocket, user_id: int, data: dict) -> None:
    chat_id = data.get("chat_id")
    payload = data.get("data") or {}
    if not chat_id:
        await websocket.send_json({"event": "error", "payload": {"detail": "Не указан chat_id"}})
        return

    async with AsyncSessionLocal() as db:
        try:
            await chat_service.ensure_member(db, chat_id, user_id)
        except ChatError as exc:
            await websocket.send_json({"event": "error", "payload": {"detail": str(exc)}})
            return

        user = await db.get(User, user_id)
        try:
            message = await message_service.create_message(
                db,
                chat_id=chat_id,
                sender_id=user_id,
                text=payload.get("text"),
                msg_type=payload.get("type", "text"),
                media_url=payload.get("media_url"),
                media_meta=payload.get("media_meta"),
                reply_to_id=payload.get("reply_to_id"),
            )
        except MessageError as exc:
            await websocket.send_json({"event": "error", "payload": {"detail": str(exc)}})
            return

        members = await chat_service.member_user_ids(db, chat_id)
        event = {
            "event": "message",
            "chat_id": chat_id,
            "payload": message_dict(message, user),
        }

    await push_to_users(members, event)
    # Отправителю тоже подтверждаем (для синхронизации между устройствами).
    await websocket.send_json(event)


@router.websocket("/ws/admin")
async def admin_ws(websocket: WebSocket, token: str = Query(default="")):
    """Канал уведомлений админ-панели (новые заказы, регистрации)."""
    from app.core.security import ACCESS_TYPE, try_decode_token

    payload = try_decode_token(token, ACCESS_TYPE)
    if not payload or payload.get("scope") != "admin":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        admin_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Админам используем отрицательное пространство id, чтобы не пересекаться с пользователями.
    shadow_id = -abs(admin_id)
    await manager.connect(shadow_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if (data or {}).get("action") == "ping":
                await websocket.send_json({"event": "pong", "payload": {}})
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(shadow_id, websocket)
