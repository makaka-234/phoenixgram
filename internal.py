"""Внутренние эндпоинты для Telegram-бота (защищены X-Bot-Token)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import verify_bot_token
from app.models.admin import Admin
from app.models.commerce import Gift, Product
from app.models.enums import AdminRole, OrderStatus
from app.models.user import User
from app.schemas.admin import AdminOut, StatsOut
from app.schemas.gift import GiftOut
from app.schemas.product import ProductOut
from app.schemas.user import UserMe
from app.services import order_service
from app.services.order_service import OrderError

router = APIRouter(prefix="/internal", tags=["Внутренние (бот)"], dependencies=[Depends(verify_bot_token)])


class FulfillRequest(BaseModel):
    tg_id: int
    product_code: str
    amount_xtr: int = Field(ge=0)
    charge_id: str
    provider_charge_id: str | None = None
    meta: dict | None = None


class StarsChangeRequest(BaseModel):
    tg_id: int
    amount: int
    reason: str = Field("Ручная корректировка", max_length=255)
    admin_tg_id: int | None = None


class AdminByTgRequest(BaseModel):
    tg_id: int
    username: str | None = None
    role: str = Field("admin", pattern="^(owner|admin|moderator)$")


@router.get("/products", response_model=list[ProductOut], summary="Товары (все активные)")
async def products(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Product).where(Product.is_active.is_(True)).order_by(Product.sort_order)
        )
    ).scalars().all()
    return [ProductOut.model_validate(p, from_attributes=True) for p in rows]


@router.get("/gifts", response_model=list[GiftOut], summary="Подарки (каталог)")
async def gifts(db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Gift).where(Gift.is_active.is_(True)).order_by(Gift.sort_order)
        )
    ).scalars().all()
    return [GiftOut.model_validate(g, from_attributes=True) for g in rows]


@router.get("/user/{tg_id}", response_model=UserMe, summary="Пользователь по tg_id")
async def user_by_tg(tg_id: int, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.tg_id == tg_id))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user


@router.post("/orders/fulfill", summary="Оплата получена — выдать товар")
async def fulfill(payload: FulfillRequest, db: AsyncSession = Depends(get_db)):
    try:
        order = await order_service.fulfill_payment(
            db,
            tg_id=payload.tg_id,
            product_code=payload.product_code,
            amount_xtr=payload.amount_xtr,
            charge_id=payload.charge_id,
            provider_charge_id=payload.provider_charge_id,
            meta=payload.meta,
        )
    except OrderError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {
        "ok": True,
        "order_id": order.id,
        "status": order.status,
        "product": order.product_title,
    }


@router.post("/stars/change", summary="Начислить/списать звёзды (из бота)")
async def stars_change(payload: StarsChangeRequest, db: AsyncSession = Depends(get_db)):
    admin_id = None
    if payload.admin_tg_id:
        admin = (
            await db.execute(select(Admin).where(Admin.tg_id == payload.admin_tg_id))
        ).scalar_one_or_none()
        if admin is not None:
            admin_id = admin.id
    try:
        user = await order_service.grant_stars_by_tg(
            db, tg_id=payload.tg_id, amount=payload.amount, reason=payload.reason, admin_id=admin_id
        )
    except OrderError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return {"ok": True, "phoenix_id": user.phoenix_id, "stars_balance": user.stars_balance}


@router.get("/stats", response_model=StatsOut, summary="Статистика (для бота)")
async def stats(db: AsyncSession = Depends(get_db)):
    from app.models.chat import Chat
    from app.models.commerce import GiftSend, Transaction
    from app.models.message import Message

    async def count(stmt) -> int:
        return int((await db.execute(stmt)).scalar() or 0)

    total_users = await count(select(func.count(User.id)))
    premium_users = await count(select(func.count(User.id)).where(User.is_premium.is_(True)))
    verified_users = await count(select(func.count(User.id)).where(User.is_verified.is_(True)))
    banned_users = await count(select(func.count(User.id)).where(User.is_banned.is_(True)))
    total_chats = await count(select(func.count(Chat.id)))
    total_messages = await count(select(func.count(Message.id)))

    from app.models.commerce import Order

    orders_total = await count(select(func.count(Order.id)))
    orders_paid = await count(select(func.count(Order.id)).where(Order.status == OrderStatus.PAID))
    revenue = int(
        (
            await db.execute(
                select(func.coalesce(func.sum(Order.amount_xtr), 0)).where(
                    Order.status == OrderStatus.PAID
                )
            )
        ).scalar()
        or 0
    )
    circulation = int(
        (await db.execute(select(func.coalesce(func.sum(User.stars_balance), 0)))).scalar() or 0
    )
    gifts_sent = await count(select(func.count(GiftSend.id)))

    return StatsOut(
        total_users=total_users,
        active_users_24h=0,
        premium_users=premium_users,
        verified_users=verified_users,
        banned_users=banned_users,
        total_chats=total_chats,
        total_messages=total_messages,
        total_orders=orders_total,
        paid_orders=orders_paid,
        revenue_xtr=revenue,
        stars_in_circulation=circulation,
        gifts_sent=gifts_sent,
    )


@router.post("/admins/by-tg", response_model=AdminOut, summary="Добавить админа по Telegram ID")
async def add_admin_by_tg(payload: AdminByTgRequest, db: AsyncSession = Depends(get_db)):
    existing = (
        await db.execute(select(Admin).where(Admin.tg_id == payload.tg_id))
    ).scalar_one_or_none()
    if existing is not None:
        existing.role = payload.role
        existing.is_active = True
        await db.commit()
        await db.refresh(existing)
        return AdminOut.model_validate(existing, from_attributes=True)

    user = (await db.execute(select(User).where(User.tg_id == payload.tg_id))).scalar_one_or_none()
    username = payload.username or (f"tg{payload.tg_id}")

    from app.core.security import hash_password
    import secrets

    admin = Admin(
        tg_id=payload.tg_id,
        user_id=user.id if user else None,
        username=username,
        password_hash=hash_password(secrets.token_urlsafe(24)),
        role=payload.role if payload.role in AdminRole.ALL else AdminRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    return AdminOut.model_validate(admin, from_attributes=True)
