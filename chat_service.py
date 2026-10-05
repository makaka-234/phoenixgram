"""Сервис чатов: создание, участники, проверки доступа."""
from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat, ChatMember
from app.models.enums import ChatType, MemberRole
from app.models.message import Message
from app.models.user import User


class ChatError(Exception):
    pass


async def get_membership(db: AsyncSession, chat_id: int, user_id: int) -> Optional[ChatMember]:
    return (
        await db.execute(
            select(ChatMember).where(
                ChatMember.chat_id == chat_id, ChatMember.user_id == user_id
            )
        )
    ).scalar_one_or_none()


async def ensure_member(db: AsyncSession, chat_id: int, user_id: int) -> ChatMember:
    member = await get_membership(db, chat_id, user_id)
    if member is None:
        raise ChatError("Вы не участник этого чата")
    return member


async def create_private_chat(db: AsyncSession, user: User, peer_phoenix_id: str) -> Chat:
    peer = (
        await db.execute(
            select(User).where(func.lower(User.phoenix_id) == peer_phoenix_id.lower())
        )
    ).scalar_one_or_none()
    if peer is None:
        raise ChatError("Пользователь не найден")
    if peer.id == user.id:
        raise ChatError("Нельзя создать чат с самим собой")

    # Ищем существующий личный чат между двумя пользователями.
    sub_a = select(ChatMember.chat_id).where(ChatMember.user_id == user.id)
    sub_b = select(ChatMember.chat_id).where(ChatMember.user_id == peer.id)
    existing = (
        await db.execute(
            select(Chat)
            .where(Chat.type == ChatType.PRIVATE, Chat.id.in_(sub_a), Chat.id.in_(sub_b))
        )
    ).scalars().first()
    if existing:
        return existing

    chat = Chat(type=ChatType.PRIVATE, owner_id=user.id)
    db.add(chat)
    await db.flush()
    db.add_all(
        [
            ChatMember(chat_id=chat.id, user_id=user.id, role=MemberRole.MEMBER),
            ChatMember(chat_id=chat.id, user_id=peer.id, role=MemberRole.MEMBER),
        ]
    )
    await db.commit()
    await db.refresh(chat)
    return chat


async def create_group(
    db: AsyncSession,
    owner: User,
    title: str,
    description: Optional[str],
    member_ids: Iterable[int],
    chat_type: str = ChatType.GROUP,
) -> Chat:
    if not title or not title.strip():
        raise ChatError("Укажите название чата")

    chat = Chat(type=chat_type, title=title.strip(), description=description, owner_id=owner.id)
    db.add(chat)
    await db.flush()

    ids = {owner.id}
    for mid in member_ids:
        ids.add(int(mid))

    # Проверяем, что пользователи существуют.
    users = (
        await db.execute(select(User.id).where(User.id.in_(ids)))
    ).scalars().all()
    valid = set(users)
    valid.add(owner.id)

    for uid in valid:
        role = MemberRole.OWNER if uid == owner.id else MemberRole.MEMBER
        db.add(ChatMember(chat_id=chat.id, user_id=uid, role=role))

    await db.commit()
    await db.refresh(chat)
    return chat


async def list_user_chats(db: AsyncSession, user_id: int) -> list[Chat]:
    stmt = (
        select(Chat)
        .join(ChatMember, ChatMember.chat_id == Chat.id)
        .where(ChatMember.user_id == user_id)
        .order_by(Chat.last_message_at.desc().nullslast(), Chat.created_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def chat_peer(db: AsyncSession, chat: Chat, user_id: int) -> Optional[User]:
    if chat.type != ChatType.PRIVATE:
        return None
    peer_member = (
        await db.execute(
            select(ChatMember).where(
                ChatMember.chat_id == chat.id, ChatMember.user_id != user_id
            )
        )
    ).scalars().first()
    if peer_member is None:
        return None
    return await db.get(User, peer_member.user_id)


async def member_user_ids(db: AsyncSession, chat_id: int) -> list[int]:
    rows = (
        await db.execute(select(ChatMember.user_id).where(ChatMember.chat_id == chat_id))
    ).scalars().all()
    return list(rows)


async def unread_count(db: AsyncSession, chat_id: int, member: ChatMember) -> int:
    stmt = select(func.count(Message.id)).where(
        Message.chat_id == chat_id, Message.is_deleted.is_(False)
    )
    if member.last_read_message_id:
        stmt = stmt.where(Message.id > member.last_read_message_id)
    if member.joined_at is not None:
        stmt = stmt.where(Message.created_at >= member.joined_at)
    return int((await db.execute(stmt)).scalar() or 0)


async def mark_read(db: AsyncSession, chat_id: int, user_id: int, message_id: int) -> None:
    member = await ensure_member(db, chat_id, user_id)
    if member.last_read_message_id is None or message_id > member.last_read_message_id:
        member.last_read_message_id = message_id
        await db.commit()


async def add_member(db: AsyncSession, chat_id: int, user_id: int, role: str = MemberRole.MEMBER) -> ChatMember:
    chat = await db.get(Chat, chat_id)
    if chat is None:
        raise ChatError("Чат не найден")
    if chat.type == ChatType.PRIVATE:
        raise ChatError("В личный чат нельзя добавлять участников")
    existing = await get_membership(db, chat_id, user_id)
    if existing:
        return existing
    member = ChatMember(chat_id=chat_id, user_id=user_id, role=role)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def remove_member(db: AsyncSession, chat_id: int, user_id: int) -> None:
    member = await ensure_member(db, chat_id, user_id)
    if member.role == MemberRole.OWNER:
        raise ChatError("Владелец не может покинуть чат — передайте права или удалите чат")
    await db.delete(member)
    await db.commit()
