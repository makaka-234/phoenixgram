"""Сообщения (REST): история, отправка, удаление."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageOut, MessagePage
from app.services import chat_service, message_service
from app.services.chat_service import ChatError
from app.services.message_service import MessageError

router = APIRouter(tags=["Сообщения"])


@router.get(
    "/chats/{chat_id}/messages",
    response_model=MessagePage,
    summary="История сообщений чата",
)
async def get_messages(
    chat_id: int,
    limit: int = Query(50, ge=1, le=100),
    before_id: int | None = Query(None, description="Подгрузить сообщения до этого id"),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await chat_service.ensure_member(db, chat_id, current.id)
    except ChatError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    messages, has_more = await message_service.list_messages(db, chat_id, limit, before_id)

    items: list[MessageOut] = []
    sender_cache: dict[int, User] = {}
    for msg in messages:
        out = MessageOut.model_validate(msg, from_attributes=True)
        if msg.sender_id:
            if msg.sender_id not in sender_cache:
                sender_cache[msg.sender_id] = await db.get(User, msg.sender_id)
            sender = sender_cache[msg.sender_id]
            if sender is not None:
                from app.schemas.user import UserShort

                out.sender = UserShort.model_validate(sender, from_attributes=True)
        items.append(out)

    return MessagePage(
        items=items,
        has_more=has_more,
        next_before_id=items[0].id if (has_more and items) else None,
    )


@router.post(
    "/chats/{chat_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
    summary="Отправить сообщение",
)
async def send_message(
    chat_id: int,
    payload: MessageCreate,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await chat_service.ensure_member(db, chat_id, current.id)
    except ChatError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    try:
        message = await message_service.create_message(
            db,
            chat_id=chat_id,
            sender_id=current.id,
            text=payload.text,
            msg_type=payload.type,
            media_url=payload.media_url,
            media_meta=payload.media_meta,
            reply_to_id=payload.reply_to_id,
        )
    except MessageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    await message_service.broadcast_new_message(db, message, current)
    out = MessageOut.model_validate(message, from_attributes=True)
    from app.schemas.user import UserShort

    out.sender = UserShort.model_validate(current, from_attributes=True)
    return out


@router.delete("/messages/{message_id}", response_model=MessageOut, summary="Удалить сообщение")
async def delete_message(
    message_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        message = await message_service.delete_message(db, message_id, current.id)
    except MessageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    from app.ws.manager import push_to_users

    ids = await chat_service.member_user_ids(db, message.chat_id)
    await push_to_users(
        ids,
        {
            "event": "message_deleted",
            "chat_id": message.chat_id,
            "payload": {"message_id": message_id},
        },
    )
    return MessageOut.model_validate(message, from_attributes=True)
