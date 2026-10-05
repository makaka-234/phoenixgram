"""Безопасность: хеширование паролей и JWT-токены."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TYPE = "access"
REFRESH_TYPE = "refresh"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def _create_token(subject: str, token_type: str, expires_delta: timedelta, extra: dict | None = None) -> str:
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str | int, extra: dict | None = None) -> str:
    return _create_token(
        subject,
        ACCESS_TYPE,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra,
    )


def create_refresh_token(subject: str | int, extra: dict | None = None) -> str:
    return _create_token(
        subject,
        REFRESH_TYPE,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        extra,
    )


def decode_token(token: str, expected_type: str | None = None) -> dict:
    """Вернуть payload токена или бросить JWTError."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    if expected_type and payload.get("type") != expected_type:
        raise JWTError(f"Ожидался токен типа '{expected_type}'")
    return payload


def try_decode_token(token: str, expected_type: str | None = None) -> Optional[dict]:
    try:
        return decode_token(token, expected_type)
    except JWTError:
        return None
