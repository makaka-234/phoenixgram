"""Чаты: список, создание, участники, прочтение."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.chat import Chat, ChatMember
from app.models.enums import ChatType, MemberRole
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import (
    ChatCreate,
    ChatDetail,
    ChatListOut,
    ChatMemberOut,
    ChatUpdate,
)
from app.schemas.user import UserShort
from app.services import chat_service
from app.services.chat_service import ChatError
from app.ws.manager import push_to_users

router = APIRouter(prefix="/chats", tags=["Чаты"])


@router.get("", response_model=list[ChatListOut], summary="Мои чаты")
async def list_chats(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    chats = await chat_service.list_user_chats(db, current.id)
    result: list[ChatListOut] = []
    for chat in chats:
        item = ChatListOut.model_validate(chat, from_attributes=True)
        peer = await chat_service.chat_peer(db, chat, current.id)
        if peer is not None:
            item.peer = UserShort.model_validate(peer, from_attributes=True)
            if not chat.title:
                item.title = peer.first_name or peer.phoenix_id
        member = await chat_service.get_membership(db, chat.id, current.id)
        if member is not None:
            item.unread_count = await chat_service.unread_count(db, chat.id, member)
        if chat.last_message_id:
            last = await db.get(Message, chat.last_message_id)
            if last is not None and not last.is_deleted:
                item.last_message_text = last.text or f"[{last.type}]"
        result.append(item)
    return result


@router.post("", response_model=ChatDetail, status_code=status.HTTP_201_CREATED, summary="Создать чат")
async def create_chat(
    payload: ChatCreate,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        if payload.type == ChatType.PRIVATE:
            if not payload.peer_phoenix_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Для личного чата укажите peer_phoenix_id",
                )
            chat = await chat_service.create_private_chat(db, current, payload.peer_phoenix_id)
        else:
            if not payload.title:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Укажите название чата",
                )
            chat = await chat_service.create_group(
                db, current, payload.title, payload.description, payload.member_ids, payload.type
            )
    except ChatError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return await _chat_detail(db, chat, current.id)


async def _chat_detail(db: AsyncSession, chat: Chat, user_id: int) -> ChatDetail:
    detail = ChatDetail.model_validate(chat, from_attributes=True)
    detail.members = [
        ChatMemberOut.model_validate(m, from_attributes=True) for m in chat.members
    ]
    peer = await chat_service.chat_peer(db, chat, user_id)
    if peer is not None:
        detail.peer = UserShort.model_validate(peer, from_attributes=True)
    member = await chat_service.get_membership(db, chat.id, user_id)
    if member is not None:
        detail.unread_count = await chat_service.unread_count(db, chat.id, member)
    return detail


@router.get("/{chat_id}", response_model=ChatDetail, summary="Детали чата")
async def get_chat(
    chat_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = await db.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Чат не найден")
    try:
        await chat_service.ensure_member(db, chat_id, current.id)
    except ChatError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return await _chat_detail(db, chat, current.id)


@router.patch("/{chat_id}", response_model=ChatDetail, summary="Изменить чат")
async def update_chat(
    chat_id: int,
    payload: ChatUpdate,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = await db.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Чат не найден")
    member = await chat_service.get_membership(db, chat_id, current.id)
    if member is None or member.role == MemberRole.MEMBER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав изменить чат")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(chat, field, value)
    await db.commit()
    await db.refresh(chat)
    return await _chat_detail(db, chat, current.id)


@router.delete("/{chat_id}", summary="Удалить/покинуть чат")
async def delete_chat(
    chat_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = await db.get(Chat, chat_id)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Чат не найден")
    member = await chat_service.get_membership(db, chat_id, current.id)
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Вы не участник чата")
    user_ids = await chat_service.member_user_ids(db, chat_id)

    if chat.type == ChatType.PRIVATE or member.role == MemberRole.OWNER:
        # Личные чаты и чаты владельца удаляем целиком.
        await db.delete(chat)
    else:
        await db.delete(member)
    await db.commit()

    await push_to_users(user_ids, {"event": "chat_deleted", "chat_id": chat_id, "payload": {}})
    return {"ok": True, "message": "Чат обновлён"}


@router.get("/{chat_id}/members", response_model=list[ChatMemberOut], summary="Участники чата")
async def chat_members(
    chat_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await chat_service.ensure_member(db, chat_id, current.id)
    rows = (
        await db.execute(select(ChatMember).where(ChatMember.chat_id == chat_id))
    ).scalars().all()
    return list(rows)


@router.post("/{chat_id}/members", response_model=ChatMemberOut, summary="Добавить участника")
async def add_chat_member(
    chat_id: int,
    user_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    member = await chat_service.get_membership(db, chat_id, current.id)
    if member is None or member.role == MemberRole.MEMBER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав добавлять участников")
    try:
        new_member = await chat_service.add_member(db, chat_id, user_id)
    except ChatError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    user_ids = await chat_service.member_user_ids(db, chat_id)
    await push_to_users(user_ids, {"event": "member_added", "chat_id": chat_id, "payload": {"user_id": user_id}})
    return new_member


@router.delete("/{chat_id}/members/{user_id}", summary="Удалить участника / выйти")
async def remove_chat_member(
    chat_id: int,
    user_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user_id != current.id:
        member = await chat_service.get_membership(db, chat_id, current.id)
        if member is None or member.role == MemberRole.MEMBER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав удалять участников")
    try:
        await chat_service.remove_member(db, chat_id, user_id)
    except ChatError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"ok": True, "message": "Участник удалён"}


@router.post("/{chat_id}/read", summary="Отметить чат прочитанным")
async def mark_read(
    chat_id: int,
    message_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await chat_service.mark_read(db, chat_id, current.id, message_id)
    except ChatError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return {"ok": True, "message": "Прочитано"}
