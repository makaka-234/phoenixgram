"""Схемы аутентификации."""
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    phoenix_id: str = Field(..., min_length=3, max_length=20, description="PhoenixGram ID")
    code: str = Field(..., min_length=4, max_length=8, description="Код от бота")


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)


class AdminToken(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    username: str
    role: str


class RegCodeCreate(BaseModel):
    """Создание кода регистрации (вызывается ботом)."""
    tg_id: int
    phoenix_id: str = Field(..., min_length=3, max_length=20)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    bonus: Optional[int] = None


class RegCodeResponse(BaseModel):
    phoenix_id: str
    code: str
    expires_in_minutes: int
    is_new_user: bool
    stars_balance: int


class LoginCodeRequest(BaseModel):
    """Запрос нового кода для входа (по tg_id)."""
    tg_id: int
