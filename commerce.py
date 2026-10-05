"""Товары, заказы, транзакции, подарки."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import OrderStatus


class Product(Base, TimestampMixin):
    """Товар магазина. Цена в Telegram Stars (XTR) и/или Звёздах Феникс."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    price_xtr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)        # цена в Telegram Stars
    phoenix_stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)    # сколько Звёзд Феникс даёт/стоит
    premium_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)               # JSON с параметрами

    emoji: Mapped[str] = mapped_column(String(8), default="⭐", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Product {self.code}>"


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (Index("ix_orders_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)

    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    product_title: Mapped[str] = mapped_column(String(128), nullable=False)
    amount_xtr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    phoenix_stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    status: Mapped[str] = mapped_column(String(16), default=OrderStatus.PENDING, nullable=False, index=True)
    tg_payment_charge_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    provider_payment_charge_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    meta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    product: Mapped[Optional["Product"]] = relationship(lazy="joined")


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
    __table_args__ = (Index("ix_transactions_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # +/- Звёзды Феникс
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    related_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    gift_send_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("admins.id", ondelete="SET NULL"), nullable=True)
    meta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Gift(Base, TimestampMixin):
    """Подарок из каталога. Цена в Звёздах Феникс."""

    __tablename__ = "gifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emoji: Mapped[str] = mapped_column(String(8), default="🎁", nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    price_stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Звёзды Феникс
    rarity: Mapped[str] = mapped_column(String(16), default="common", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class GiftSend(Base, TimestampMixin):
    __tablename__ = "gift_sends"
    __table_args__ = (Index("ix_gifts_sends_receiver", "receiver_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gift_id: Mapped[int] = mapped_column(ForeignKey("gifts.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    chat_id: Mapped[Optional[int]] = mapped_column(ForeignKey("chats.id", ondelete="SET NULL"), nullable=True)

    price_paid: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    gift: Mapped["Gift"] = relationship(lazy="joined")
