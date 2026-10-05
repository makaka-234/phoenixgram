"""Сервис сообщений."""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat, ChatMember
from app.models.enums import MessageType
from app.models.message import Message
from app.models.user import User
from app.services.chat_service import get_membership


class MessageError(Exception):
    pass


async def create_message(
    db: AsyncSession,
    *,
    chat_id: int,
    sender_id: Optional[int],
    text: Optional[str] = None,
    msg_type: str = MessageType.TEXT,
    media_url: Optional[str] = None,
    media_meta: Optional[dict] = None,
    reply_to_id: Optional[int] = None,
) -> Message:
    if msg_type not in MessageType.ALL:
        raise MessageError("Неизвестный тип сообщения")
    if not text and not media_url and msg_type not in (MessageType.STICKER, MessageType.GIFT):
        raise MessageError("Сообщение пустое")
    if msg_type == MessageType.TEXT and not sender_id:
        raise MessageError("У системного сообщения должен быть тип system")

    message = Message(
        chat_id=chat_id,
        sender_id=sender_id,
        type=msg_type,
        text=text,
        media_url=media_url,
        media_meta=json.dumps(media_meta, ensure_ascii=False) if media_meta else None,
        reply_to_id=reply_to_id,
    )
    db.add(message)
    await db.flush()

    chat = await db.get(Chat, chat_id)
    if chat is not None:
        chat.last_message_id = message.id
        chat.last_message_at = message.created_at

    await db.commit()
    await db.refresh(message)
    return message


async def list_messages(
    db: AsyncSession,
    chat_id: int,
    limit: int = 50,
    before_id: Optional[int] = None,
) -> tuple[list[Message], bool]:
    """Вернуть сообщения по убыванию id (для подгрузки «вверх»)."""
    stmt = select(Message).where(Message.chat_id == chat_id)
    if before_id:
        stmt = stmt.where(Message.id < before_id)
    stmt = stmt.order_by(Message.id.desc()).limit(limit + 1)
    rows = list((await db.execute(stmt)).scalars().all())

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]
    rows.reverse()  # вернуть в хронологическом порядке
    return rows, has_more


async def delete_message(db: AsyncSession, message_id: int, user_id: int) -> Message:
    message = await db.get(Message, message_id)
    if message is None:
        raise MessageError("Сообщение не найдено")
    if message.sender_id != user_id:
        member = await get_membership(db, message.chat_id, user_id)
        if member is None or member.role == "member":
            raise MessageError("Нет прав удалить это сообщение")
    message.is_deleted = True
    message.text = None
    await db.commit()
    await db.refresh(message)
    return message


async def system_message(db: AsyncSession, chat_id: int, text: str) -> Message:
    return await create_message(db, chat_id=chat_id, sender_id=None, text=text, msg_type=MessageType.SYSTEM)


async def get_shared_chats(db: AsyncSession, user_a: int, user_b: int) -> list[int]:
    sub_a = select(ChatMember.chat_id).where(ChatMember.user_id == user_a)
    sub_b = select(ChatMember.chat_id).where(ChatMember.user_id == user_b)
    rows = (
        await db.execute(select(Chat.id).where(Chat.id.in_(sub_a), Chat.id.in_(sub_b)))
    ).scalars().all()
    return list(rows)


async def broadcast_new_message(db: AsyncSession, message: Message, sender: Optional[User] = None) -> None:
    """Разослать событие о новом сообщении всем участникам чата через Redis/WS."""
    from app.services.chat_service import member_user_ids
    from app.ws.manager import push_to_users
    from app.ws.serialize import message_dict

    ids = await member_user_ids(db, message.chat_id)
    await push_to_users(
        ids,
        {"event": "message", "chat_id": message.chat_id, "payload": message_dict(message, sender)},
    )
