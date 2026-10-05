"""Каталог подарков и отправка подарков."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.gift import GiftOut, GiftSendOut, GiftSendRequest
from app.services import gift_service
from app.services.gift_service import GiftError
from app.ws.manager import push_to_users
from app.ws.serialize import gift_send_dict

router = APIRouter(prefix="/gifts", tags=["Подарки"])


@router.get("", response_model=list[GiftOut], summary="Каталог подарков")
async def catalog(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    gifts = await gift_service.list_catalog(db, only_active=True)
    return [GiftOut.model_validate(g, from_attributes=True) for g in gifts]


@router.post("/{gift_id}/send", response_model=GiftSendOut, summary="Отправить подарок")
async def send_gift(
    gift_id: int,
    payload: GiftSendRequest,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        send = await gift_service.send_gift(
            db,
            current,
            gift_id,
            payload.receiver_phoenix_id,
            payload.message,
            payload.is_anonymous,
        )
    except GiftError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    receiver = await db.get(User, send.receiver_id)
    await db.refresh(current)

    await push_to_users(
        [send.receiver_id],
        {
            "event": "gift_received",
            "payload": gift_send_dict(send, current, receiver),
        },
    )
    await push_to_users(
        [current.id],
        {"event": "balance_updated", "payload": {"stars_balance": current.stars_balance, "type": "gift_out"}},
    )
    out = GiftSendOut.model_validate(send, from_attributes=True)
    out.gift = GiftOut.model_validate(send.gift, from_attributes=True)
    return out


@router.get("/received", response_model=list[GiftSendOut], summary="Полученные подарки")
async def received(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = await gift_service.list_received(db, current.id)
    result = []
    for send in rows:
        out = GiftSendOut.model_validate(send, from_attributes=True)
        out.gift = GiftOut.model_validate(send.gift, from_attributes=True) if send.gift else None
        result.append(out)
    return result


@router.get("/sent", response_model=list[GiftSendOut], summary="Отправленные подарки")
async def sent(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = await gift_service.list_sent(db, current.id)
    result = []
    for send in rows:
        out = GiftSendOut.model_validate(send, from_attributes=True)
        out.gift = GiftOut.model_validate(send.gift, from_attributes=True) if send.gift else None
        result.append(out)
    return result
