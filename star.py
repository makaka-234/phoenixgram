"""Схемы Звёзд Феникс (внутренняя валюта)."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class BalanceOut(BaseModel):
    stars_balance: int
    is_premium: bool = False
    premium_until: Optional[datetime] = None


class TransferRequest(BaseModel):
    to_phoenix_id: str = Field(..., min_length=3, max_length=20)
    amount: int = Field(..., gt=0, le=1_000_000)
    comment: Optional[str] = Field(None, max_length=140)


class TransactionOut(ORMModel):
    id: int
    user_id: int
    amount: int
    balance_after: int
    type: str
    description: str
    related_user_id: Optional[int] = None
    order_id: Optional[int] = None
    created_at: datetime


class AdminStarChange(BaseModel):
    phoenix_id: Optional[str] = Field(None, max_length=20)
    user_id: Optional[int] = None
    amount: int = Field(..., description="Положительное — начислить, отрицательное — списать")
    reason: str = Field("Ручная корректировка", max_length=255)
