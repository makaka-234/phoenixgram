"""Схемы пользователя."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class UserShort(ORMModel):
    id: int
    phoenix_id: str
    first_name: str = ""
    last_name: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    is_premium: bool = False
    is_verified: bool = False
    stars_balance: int = 0


class UserPublic(ORMModel):
    id: int
    phoenix_id: str
    first_name: str = ""
    last_name: Optional[str] = None
    username: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_premium: bool = False
    is_verified: bool = False
    stars_balance: int = 0
    last_seen: Optional[datetime] = None


class UserMe(UserPublic):
    tg_id: Optional[int] = None
    premium_until: Optional[datetime] = None
    is_banned: bool = False
    created_at: datetime


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=64)
    last_name: Optional[str] = Field(None, max_length=64)
    username: Optional[str] = Field(None, min_length=3, max_length=32)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=512)
