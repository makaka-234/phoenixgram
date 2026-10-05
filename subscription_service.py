"""Сервис подписок (Феникс Премиум)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class SubscriptionError(Exception):
    pass


def is_premium_active(user: User) -> bool:
    if not user.is_premium:
        return False
    if user.premium_until is None:
        return True
    return user.premium_until > datetime.now(tz=timezone.utc)


async def grant_premium(db: AsyncSession, user: User, days: int, commit: bool = True) -> User:
    """Продлить (или выдать) Premium на N дней."""
    if days <= 0:
        raise SubscriptionError("Срок подписки должен быть больше нуля")

    now = datetime.now(tz=timezone.utc)
    base = user.premium_until if (user.premium_until and user.premium_until > now) else now
    user.premium_until = base + timedelta(days=days)
    user.is_premium = True

    if commit:
        await db.commit()
        await db.refresh(user)
    else:
        await db.flush()
    return user


async def revoke_premium(db: AsyncSession, user: User, commit: bool = True) -> User:
    user.is_premium = False
    user.premium_until = None
    if commit:
        await db.commit()
        await db.refresh(user)
    else:
        await db.flush()
    return user


async def refresh_status(db: AsyncSession, user: User) -> User:
    """Снять Premium, если срок истёк."""
    if user.is_premium and user.premium_until and user.premium_until <= datetime.now(tz=timezone.utc):
        user.is_premium = False
        await db.commit()
        await db.refresh(user)
    return user
