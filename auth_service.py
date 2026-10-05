"""Сервис регистрации и входа.

Поток:
 1. Бот вызывает `register_or_get_code(...)` — проверяет уникальность ID,
    создаёт пользователя (если нужно) с бонусом и выдаёт 8-значный код.
 2. Приложение отправляет ID + код → получает JWT.
"""
from __future__ import annotations

import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.enums import TransactionType
from app.models.user import RegCode, User
from app.services.star_service import change_balance

PHOENIX_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,19}$")
RESERVED_IDS = {"admin", "root", "support", "phoenixgram", "system", "owner", "moderator"}


class AuthError(Exception):
    """Ошибка аутентификации/регистрации."""


def validate_phoenix_id(value: str) -> str:
    value = (value or "").strip().lstrip("@")
    if not PHOENIX_ID_RE.match(value):
        raise AuthError(
            "ID должен быть на латинице, начинаться с буквы, 3–20 символов "
            "(буквы, цифры и «_»)."
        )
    if value.lower() in RESERVED_IDS:
        raise AuthError("Этот ID зарезервирован. Выберите другой.")
    return value


def generate_code() -> str:
    return f"{secrets.randbelow(100_000_000):08d}"


async def is_phoenix_id_taken(db: AsyncSession, phoenix_id: str) -> bool:
    result = await db.execute(
        select(func.count(User.id)).where(func.lower(User.phoenix_id) == phoenix_id.lower())
    )
    return int(result.scalar() or 0) > 0


async def register_or_get_code(
    db: AsyncSession,
    *,
    tg_id: int,
    phoenix_id: str,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    username: Optional[str] = None,
    bonus: Optional[int] = None,
) -> dict:
    """Зарегистрировать пользователя из бота и выдать код входа."""
    phoenix_id = validate_phoenix_id(phoenix_id)

    # Пользователь уже с таким tg_id?
    existing_by_tg = (
        await db.execute(select(User).where(User.tg_id == tg_id))
    ).scalar_one_or_none()

    is_new_user = False

    if existing_by_tg is not None:
        if existing_by_tg.phoenix_id.lower() != phoenix_id.lower():
            raise AuthError(
                f"Вы уже зарегистрированы под ID @{existing_by_tg.phoenix_id}. "
                "Сменить ID нельзя — запросите код для входа."
            )
        user = existing_by_tg
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if username is not None:
            user.username = username
    else:
        if await is_phoenix_id_taken(db, phoenix_id):
            raise AuthError(f"ID @{phoenix_id} уже занят. Выберите другой.")
        is_new_user = True
        user = User(
            phoenix_id=phoenix_id,
            tg_id=tg_id,
            first_name=(first_name or "").strip(),
            last_name=last_name,
            username=username,
            stars_balance=0,
        )
        db.add(user)
        await db.flush()

        start_bonus = settings.NEW_USER_BONUS if bonus is None else bonus
        if start_bonus:
            await change_balance(
                db,
                user.id,
                start_bonus,
                TransactionType.BONUS,
                "Бонус за регистрацию в PhoenixGram",
                commit=False,
            )

    code = await issue_code(db, user, commit=False)
    await db.commit()
    await db.refresh(user)

    return {
        "user": user,
        "code": code.code,
        "expires_in_minutes": settings.REG_CODE_TTL_MINUTES,
        "is_new_user": is_new_user,
    }


async def issue_code(db: AsyncSession, user: User, commit: bool = True) -> RegCode:
    """Создать новый 8-значный код входа (аннулирует прежние неиспользованные)."""
    now = datetime.now(tz=timezone.utc)

    old = (
        await db.execute(
            select(RegCode).where(
                RegCode.user_id == user.id,
                RegCode.is_used.is_(False),
                RegCode.expires_at > now,
            )
        )
    ).scalars().all()
    for item in old:
        item.is_used = True

    code = RegCode(
        user_id=user.id,
        phoenix_id=user.phoenix_id,
        tg_id=user.tg_id,
        code=generate_code(),
        expires_at=now + timedelta(minutes=settings.REG_CODE_TTL_MINUTES),
        is_used=False,
    )
    db.add(code)
    if commit:
        await db.commit()
        await db.refresh(code)
    else:
        await db.flush()
    return code


async def get_user_by_tg_id(db: AsyncSession, tg_id: int) -> Optional[User]:
    return (await db.execute(select(User).where(User.tg_id == tg_id))).scalar_one_or_none()


async def get_user_by_phoenix_id(db: AsyncSession, phoenix_id: str) -> Optional[User]:
    return (
        await db.execute(select(User).where(func.lower(User.phoenix_id) == phoenix_id.lower()))
    ).scalar_one_or_none()


async def login_with_code(db: AsyncSession, phoenix_id: str, code: str) -> dict:
    """Вход: проверить ID + код, вернуть пару токенов."""
    user = await get_user_by_phoenix_id(db, phoenix_id.strip().lstrip("@"))
    if user is None:
        raise AuthError("Пользователь с таким ID не найден")
    if user.is_banned:
        raise AuthError("Аккаунт заблокирован")

    now = datetime.now(tz=timezone.utc)
    reg_code = (
        await db.execute(
            select(RegCode)
            .where(
                RegCode.user_id == user.id,
                RegCode.code == code.strip(),
                RegCode.is_used.is_(False),
                RegCode.expires_at > now,
            )
            .order_by(RegCode.created_at.desc())
        )
    ).scalars().first()

    if reg_code is None:
        raise AuthError("Неверный или истёкший код. Запросите новый код в боте.")

    reg_code.is_used = True
    reg_code.used_at = now
    user.last_seen = now
    await db.commit()

    return {
        "user": user,
        "access_token": create_access_token(user.id, {"scope": "user", "pid": user.phoenix_id}),
        "refresh_token": create_refresh_token(user.id, {"scope": "user"}),
    }
