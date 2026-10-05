"""Схемы админ-панели."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class AdminOut(ORMModel):
    id: int
    tg_id: Optional[int] = None
    user_id: Optional[int] = None
    username: str
    role: str
    is_active: bool
    created_at: datetime


class AdminCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    role: str = Field("admin", pattern="^(owner|admin|moderator)$")
    tg_id: Optional[int] = None


class AdminUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    role: Optional[str] = Field(None, pattern="^(owner|admin|moderator)$")
    is_active: Optional[bool] = None


class AdminLogOut(ORMModel):
    id: int
    admin_id: Optional[int] = None
    admin_username: str
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime


class UserAdminUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=64)
    username: Optional[str] = Field(None, max_length=32)
    is_premium: Optional[bool] = None
    premium_until: Optional[datetime] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class BanRequest(BaseModel):
    is_banned: bool
    reason: Optional[str] = Field(None, max_length=255)


class StatsOut(BaseModel):
    total_users: int
    active_users_24h: int
    premium_users: int
    verified_users: int
    banned_users: int
    total_chats: int
    total_messages: int
    total_orders: int
    paid_orders: int
    revenue_xtr: int
    stars_in_circulation: int
    gifts_sent: int
