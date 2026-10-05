"""Сервис Звёзд Феникс: баланс, транзакции, переводы.

ВАЖНО: Звёзды Феникс — внутренняя валюта. Вывод средств невозможен.
Все изменения баланса проходят только через этот сервис, чтобы
баланс и история транзакций всегда были согласованы.
"""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import Transaction
from app.models.enums import TransactionType
from app.models.user import User


class StarError(Exception):
    """Ошибка операций со звёздами."""


async def _locked_user(db: AsyncSession, user_id: int) -> User:
    """Получить пользователя с блокировкой строки (защита от гонок)."""
    result = await db.execute(select(User).where(User.id == user_id).with_for_update())
    user = result.scalar_one_or_none()
    if user is None:
        raise StarError("Пользователь не найден")
    return user


async def change_balance(
    db: AsyncSession,
    user_id: int,
    amount: int,
    tx_type: str,
    description: str = "",
    *,
    related_user_id: Optional[int] = None,
    order_id: Optional[int] = None,
    gift_send_id: Optional[int] = None,
    admin_id: Optional[int] = None,
    meta: Optional[dict] = None,
    allow_negative: bool = False,
    commit: bool = True,
) -> Transaction:
    """Изменить баланс и записать транзакцию. amount может быть отрицательным."""
    if amount == 0:
        raise StarError("Сумма операции не может быть нулевой")
    if tx_type not in TransactionType.ALL:
        raise StarError(f"Неизвестный тип транзакции: {tx_type}")

    user = await _locked_user(db, user_id)
    new_balance = user.stars_balance + amount
    if new_balance < 0 and not allow_negative:
        raise StarError("Недостаточно Звёзд Феникс на балансе")

    user.stars_balance = new_balance

    tx = Transaction(
        user_id=user_id,
        amount=amount,
        balance_after=new_balance,
        type=tx_type,
        description=description[:255],
        related_user_id=related_user_id,
        order_id=order_id,
        gift_send_id=gift_send_id,
        admin_id=admin_id,
        meta=json.dumps(meta, ensure_ascii=False) if meta else None,
    )
    db.add(tx)
    await db.flush()

    if commit:
        await db.commit()
        await db.refresh(user)
    return tx


async def get_balance(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(select(User.stars_balance).where(User.id == user_id))
    value = result.scalar_one_or_none()
    return int(value or 0)


async def transfer(
    db: AsyncSession,
    sender_id: int,
    receiver_phoenix_id: str,
    amount: int,
    comment: str | None = None,
) -> tuple[Transaction, Transaction]:
    """Перевод звёзд между пользователями (без вывода средств)."""
    if amount <= 0:
        raise StarError("Сумма перевода должна быть больше нуля")

    result = await db.execute(
        select(User).where(func.lower(User.phoenix_id) == receiver_phoenix_id.lower())
    )
    receiver = result.scalar_one_or_none()
    if receiver is None:
        raise StarError("Получатель не найден")
    if receiver.id == sender_id:
        raise StarError("Нельзя перевести звёзды самому себе")
    if receiver.is_banned:
        raise StarError("Получатель заблокирован")

    sender = await _locked_user(db, sender_id)
    if sender.stars_balance < amount:
        raise StarError("Недостаточно Звёзд Феникс на балансе")

    desc_out = comment or f"Перевод пользователю @{receiver.phoenix_id}"
    desc_in = comment or f"Перевод от @{sender.phoenix_id}"

    tx_out = await change_balance(
        db, sender_id, -amount, TransactionType.TRANSFER_OUT, desc_out,
        related_user_id=receiver.id, commit=False,
    )
    tx_in = await change_balance(
        db, receiver.id, amount, TransactionType.TRANSFER_IN, desc_in,
        related_user_id=sender_id, commit=False,
    )
    await db.commit()
    await db.refresh(tx_out)
    await db.refresh(tx_in)
    return tx_out, tx_in


async def list_transactions(
    db: AsyncSession,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    tx_type: Optional[str] = None,
) -> tuple[list[Transaction], int]:
    stmt = select(Transaction).where(Transaction.user_id == user_id)
    count_stmt = select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
    if tx_type:
        stmt = stmt.where(Transaction.type == tx_type)
        count_stmt = count_stmt.where(Transaction.type == tx_type)

    stmt = stmt.order_by(Transaction.created_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    total = int((await db.execute(count_stmt)).scalar() or 0)
    return list(rows), total


async def total_in_circulation(db: AsyncSession) -> int:
    """Суммарное количество Звёзд Феникс у всех пользователей."""
    result = await db.execute(select(func.coalesce(func.sum(User.stars_balance), 0)))
    return int(result.scalar() or 0)
