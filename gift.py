"""Схемы подарков."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel
from app.schemas.user import UserShort


class GiftOut(ORMModel):
    id: int
    code: str
    title: str
    description: Optional[str] = None
    emoji: str
    image_url: Optional[str] = None
    price_stars: int
    rarity: str
    is_active: bool
    sort_order: int


class GiftCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=64)
    title: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=500)
    emoji: str = Field("🎁", max_length=8)
    image_url: Optional[str] = Field(None, max_length=512)
    price_stars: int = Field(0, ge=0)
    rarity: str = Field("common", max_length=16)
    is_active: bool = True
    sort_order: int = 0


class GiftUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = Field(None, max_length=500)
    emoji: Optional[str] = Field(None, max_length=8)
    image_url: Optional[str] = Field(None, max_length=512)
    price_stars: Optional[int] = Field(None, ge=0)
    rarity: Optional[str] = Field(None, max_length=16)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class GiftSendRequest(BaseModel):
    receiver_phoenix_id: str = Field(..., min_length=3, max_length=20)
    message: Optional[str] = Field(None, max_length=255)
    is_anonymous: bool = False


class GiftSendOut(ORMModel):
    id: int
    gift_id: int
    sender_id: int
    receiver_id: int
    price_paid: int
    message: Optional[str] = None
    is_anonymous: bool = False
    created_at: datetime
    gift: Optional[GiftOut] = None
    sender: Optional[UserShort] = None
    receiver: Optional[UserShort] = None
