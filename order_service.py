"""Сервис заказов: выдача товаров после оплаты Telegram Stars (XTR)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import Order, Product
from app.models.enums import OrderStatus, ProductType, TransactionType
from app.models.user import User
from app.services import subscription_service
from app.services.star_service import change_balance
from app.ws.manager import push_to_users


class OrderError(Exception):
    pass


async def get_product(db: AsyncSession, code: str) -> Optional[Product]:
    return (
        await db.execute(select(Product).where(Product.code == code))
    ).scalar_one_or_none()


async def apply_product(db: AsyncSession, user: User, product: Product, order: Order, commit: bool = True) -> None:
    """Применить эффект товара к пользователю."""
    payload: dict = {}
    if product.payload:
        try:
            payload = json.loads(product.payload)
        except (ValueError, TypeError):
            payload = {}

    if product.type == ProductType.STARS:
        if product.phoenix_stars:
            await change_balance(
                db,
                user.id,
                product.phoenix_stars,
                TransactionType.PURCHASE_IN,
                f"Покупка {product.phoenix_stars} Звёзд Феникс",
                order_id=order.id,
                commit=False,
            )

    elif product.type == ProductType.PREMIUM:
        days = product.premium_days or int(payload.get("days", 30))
        await subscription_service.grant_premium(db, user, days, commit=False)

    elif product.type == ProductType.USERNAME:
        desired = payload.get("username")
        if desired:
            taken = (
                await db.execute(
                    select(func.count(User.id)).where(
                        func.lower(User.username) == str(desired).lower(), User.id != user.id
                    )
                )
            ).scalar()
            if not taken:
                user.username = str(desired).lstrip("@")[:32]

    elif product.type == ProductType.VERIFICATION:
        user.is_verified = True

    if commit:
        await db.commit()
        await db.refresh(user)
    else:
        await db.flush()


async def fulfill_payment(
    db: AsyncSession,
    *,
    tg_id: int,
    product_code: str,
    amount_xtr: int,
    charge_id: str,
    provider_charge_id: Optional[str] = None,
    meta: Optional[dict] = None,
) -> Order:
    """Провести оплату: создать оплаченный заказ и выдать товар.

    Идемпотентно: повторный вызов с тем же charge_id возвращает существующий заказ.
    """
    existing = (
        await db.execute(select(Order).where(Order.tg_payment_charge_id == charge_id))
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    user = (
        await db.execute(select(User).where(User.tg_id == tg_id))
    ).scalar_one_or_none()
    if user is None:
        raise OrderError("Сначала зарегистрируйтесь в PhoenixGram (меню «Регистрация»)")
    if user.is_banned:
        raise OrderError("Аккаунт заблокирован")

    product = await get_product(db, product_code)
    if product is None or not product.is_active:
        raise OrderError("Товар недоступен")

    order = Order(
        user_id=user.id,
        product_id=product.id,
        product_code=product.code,
        product_title=product.title,
        amount_xtr=amount_xtr,
        phoenix_stars=product.phoenix_stars,
        status=OrderStatus.PAID,
        tg_payment_charge_id=charge_id,
        provider_payment_charge_id=provider_charge_id,
        meta=json.dumps(meta, ensure_ascii=False) if meta else None,
        paid_at=datetime.now(tz=timezone.utc),
    )
    db.add(order)
    await db.flush()

    await apply_product(db, user, product, order, commit=False)
    await db.commit()
    await db.refresh(order)
    await db.refresh(user)

    payload = {
        "stars_balance": user.stars_balance,
        "is_premium": user.is_premium,
        "product": product.title,
    }
    await push_to_users(
        [user.id],
        {"event": "order_paid", "payload": payload},
    )
    return order


async def grant_stars_by_tg(
    db: AsyncSession,
    *,
    tg_id: int,
    amount: int,
    reason: str = "Начисление",
    admin_id: Optional[int] = None,
) -> User:
    user = (
        await db.execute(select(User).where(User.tg_id == tg_id))
    ).scalar_one_or_none()
    if user is None:
        raise OrderError("Пользователь не найден")

    tx_type = TransactionType.ADMIN_CREDIT if amount >= 0 else TransactionType.ADMIN_DEBIT
    await change_balance(
        db,
        user.id,
        amount,
        tx_type,
        reason,
        admin_id=admin_id,
    )
    await db.refresh(user)
    await push_to_users(
        [user.id],
        {"event": "balance_updated", "payload": {"stars_balance": user.stars_balance, "type": tx_type}},
    )
    return user
