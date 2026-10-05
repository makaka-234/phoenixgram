"""Подписки (Феникс Премиум) и магазин товаров для приложения."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.commerce import Product
from app.models.user import User
from app.schemas.product import ProductOut
from app.services import subscription_service

router = APIRouter(tags=["Подписки и магазин"])


@router.get("/subscriptions/me", summary="Статус моей подписки Premium")
async def my_subscription(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await subscription_service.refresh_status(db, current)
    return {
        "is_premium": current.is_premium,
        "premium_until": current.premium_until,
        "is_verified": current.is_verified,
    }


@router.get("/shop/products", response_model=list[ProductOut], summary="Товары магазина")
async def shop_products(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Product)
        .where(Product.is_active.is_(True))
        .order_by(Product.sort_order.asc(), Product.price_xtr.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [ProductOut.model_validate(p, from_attributes=True) for p in rows]
