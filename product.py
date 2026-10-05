"""Схемы товаров и заказов."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ProductOut(ORMModel):
    id: int
    code: str
    title: str
    description: Optional[str] = None
    type: str
    price_xtr: int
    phoenix_stars: int
    premium_days: int
    emoji: str
    is_active: bool
    sort_order: int


class ProductCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=64)
    title: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=1000)
    type: str = Field(..., pattern="^(stars|premium|username|verification)$")
    price_xtr: int = Field(0, ge=0)
    phoenix_stars: int = Field(0, ge=0)
    premium_days: int = Field(0, ge=0)
    emoji: str = Field("⭐", max_length=8)
    is_active: bool = True
    sort_order: int = 0
    payload: Optional[dict] = None


class ProductUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = Field(None, max_length=1000)
    price_xtr: Optional[int] = Field(None, ge=0)
    phoenix_stars: Optional[int] = Field(None, ge=0)
    premium_days: Optional[int] = Field(None, ge=0)
    emoji: Optional[str] = Field(None, max_length=8)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    payload: Optional[dict] = None


class OrderOut(ORMModel):
    id: int
    user_id: int
    product_id: Optional[int] = None
    product_code: str
    product_title: str
    amount_xtr: int
    phoenix_stars: int
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None
