"""Экспорт сервисов."""
from app.services import (
    admin_service,
    auth_service,
    chat_service,
    gift_service,
    message_service,
    order_service,
    star_service,
    subscription_service,
)

__all__ = [
    "admin_service",
    "auth_service",
    "chat_service",
    "gift_service",
    "message_service",
    "order_service",
    "star_service",
    "subscription_service",
]
