"""FastAPI-зависимости: текущий пользователь, администратор, роли."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import ACCESS_TYPE, try_decode_token
from app.models.admin import Admin
from app.models.enums import AdminRole
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация")

    payload = try_decode_token(credentials.credentials, ACCESS_TYPE)
    if not payload or payload.get("scope") == "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")

    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт заблокирован")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Аккаунт отключён")
    return user


async def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Admin:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация администратора")

    payload = try_decode_token(credentials.credentials, ACCESS_TYPE)
    if not payload or payload.get("scope") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен администратора")

    admin = await db.get(Admin, int(payload["sub"]))
    if admin is None or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещён")
    return admin


def require_admin_role(*roles: str):
    """Фабрика зависимости: доступ только для указанных ролей."""
    allowed = set(roles)

    async def _checker(admin: Admin = Depends(get_current_admin)) -> Admin:
        if allowed and admin.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется роль: {', '.join(sorted(allowed))}",
            )
        return admin

    return _checker


require_owner = require_admin_role(AdminRole.OWNER)
require_admin_or_owner = require_admin_role(AdminRole.OWNER, AdminRole.ADMIN)


def get_client_ip(x_forwarded_for: Optional[str] = Header(default=None)) -> Optional[str]:
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return None


async def verify_bot_token(
    x_bot_token: Optional[str] = Header(default=None, alias="X-Bot-Token"),
) -> None:
    """Проверка общего секрета для внутренних запросов от бота."""
    from app.core.config import settings

    if not settings.BOT_TOKEN or x_bot_token != settings.BOT_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный токен бота")


def require_ws_token(token: Optional[str]) -> int:
    """Извлечь user_id из токена для WebSocket (токен в query)."""
    from app.core.security import ACCESS_TYPE, try_decode_token

    payload = try_decode_token(token or "", ACCESS_TYPE)
    if not payload or payload.get("scope") == "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")
    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")
