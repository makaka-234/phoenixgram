"""Звёзды Феникс: баланс, история, переводы.

Звёзды Феникс — внутренняя валюта, вывод средств невозможен.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.commerce import Transaction
from app.models.user import User
from app.schemas.common import Page
from app.schemas.star import BalanceOut, TransactionOut, TransferRequest
from app.services import star_service, subscription_service
from app.services.star_service import StarError
from app.ws.manager import push_to_users

router = APIRouter(prefix="/stars", tags=["Звёзды Феникс"])


@router.get("/balance", response_model=BalanceOut, summary="Мой баланс звёзд")
async def get_balance(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await subscription_service.refresh_status(db, current)
    return BalanceOut(
        stars_balance=current.stars_balance,
        is_premium=current.is_premium,
        premium_until=current.premium_until,
    )


@router.get("/transactions", response_model=Page[TransactionOut], summary="История операций")
async def transactions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    type: str | None = Query(None, description="Фильтр по типу транзакции"),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await star_service.list_transactions(db, current.id, limit, offset, type)
    return Page[TransactionOut](
        items=[TransactionOut.model_validate(r, from_attributes=True) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/transfer", response_model=TransactionOut, summary="Перевести звёзды другому пользователю")
async def transfer(
    payload: TransferRequest,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        tx_out, _ = await star_service.transfer(
            db, current.id, payload.to_phoenix_id, payload.amount, payload.comment
        )
    except StarError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Обновим данные получателя и оповестим обе стороны через WebSocket.
    receiver = (
        await db.execute(
            select(User).where(User.phoenix_id == payload.to_phoenix_id.lstrip("@"))
        )
    ).scalar_one_or_none()
    if receiver is not None:
        await push_to_users(
            [receiver.id],
            {
                "event": "balance_updated",
                "payload": {"stars_balance": receiver.stars_balance, "type": "transfer_in"},
            },
        )
    await db.refresh(current)
    await push_to_users(
        [current.id],
        {
            "event": "balance_updated",
            "payload": {"stars_balance": current.stars_balance, "type": "transfer_out"},
        },
    )
    return TransactionOut.model_validate(tx_out, from_attributes=True)
