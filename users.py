"""Пользователи: профиль, поиск."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserMe, UserPublic, UserShort, UserUpdate
from app.services import subscription_service
from app.ws.manager import manager

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.get("/me", response_model=UserMe, summary="Мой профиль")
async def get_me(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await subscription_service.refresh_status(db, current)
    return current


@router.patch("/me", response_model=UserMe, summary="Обновить профиль")
async def update_me(
    payload: UserUpdate,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)
    if "username" in data and data["username"]:
        exists = (
            await db.execute(
                select(func.count(User.id)).where(
                    func.lower(User.username) == data["username"].lower(), User.id != current.id
                )
            )
        ).scalar()
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Юзернейм уже занят")
    for field, value in data.items():
        setattr(current, field, value)
    await db.commit()
    await db.refresh(current)
    return current


@router.get("/search", response_model=list[UserShort], summary="Поиск пользователей")
async def search_users(
    q: str = Query(..., min_length=1, max_length=64),
    limit: int = Query(20, ge=1, le=50),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pattern = f"%{q.strip().lstrip('@')}%"
    stmt = (
        select(User)
        .where(
            User.id != current.id,
            User.is_active.is_(True),
            User.is_banned.is_(False),
            or_(
                User.phoenix_id.ilike(pattern),
                User.username.ilike(pattern),
                User.first_name.ilike(pattern),
            ),
        )
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


@router.get("/online", response_model=list[int], summary="ID пользователей онлайн")
async def online_users(current: User = Depends(get_current_user)):
    return manager.online_user_ids()


@router.get("/{phoenix_id}", response_model=UserPublic, summary="Профиль по PhoenixGram ID")
async def get_user(
    phoenix_id: str,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = (
        await db.execute(
            select(User).where(func.lower(User.phoenix_id) == phoenix_id.strip().lstrip("@").lower())
        )
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return user
