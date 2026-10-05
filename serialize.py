"""Сериализация моделей для WebSocket-событий (plain dict)."""
from __future__ import annotations

from typing import Optional

from app.models.commerce import GiftSend
from app.models.message import Message
from app.models.user import User


def user_short(user: Optional[User]) -> Optional[dict]:
    if user is None:
        return None
    return {
        "id": user.id,
        "phoenix_id": user.phoenix_id,
        "first_name": user.first_name or "",
        "last_name": user.last_name,
        "username": user.username,
        "avatar_url": user.avatar_url,
        "is_premium": bool(user.is_premium),
        "is_verified": bool(user.is_verified),
        "stars_balance": user.stars_balance,
    }


def message_dict(message: Message, sender: Optional[User] = None) -> dict:
    meta = None
    if message.media_meta:
        import json

        try:
            meta = json.loads(message.media_meta)
        except (ValueError, TypeError):
            meta = None

    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "type": message.type,
        "text": message.text,
        "media_url": message.media_url,
        "media_meta": meta,
        "reply_to_id": message.reply_to_id,
        "is_edited": message.is_edited,
        "is_deleted": message.is_deleted,
        "created_at": message.created_at.isoformat() if message.created_at else None,
        "edited_at": message.edited_at.isoformat() if message.edited_at else None,
        "sender": user_short(sender),
    }


def gift_send_dict(send: GiftSend, sender: Optional[User] = None, receiver: Optional[User] = None) -> dict:
    return {
        "id": send.id,
        "gift_id": send.gift_id,
        "sender_id": send.sender_id,
        "receiver_id": send.receiver_id,
        "price_paid": send.price_paid,
        "message": send.message,
        "is_anonymous": send.is_anonymous,
        "created_at": send.created_at.isoformat() if send.created_at else None,
        "gift": {
            "id": send.gift.id,
            "code": send.gift.code,
            "title": send.gift.title,
            "emoji": send.gift.emoji,
            "image_url": send.gift.image_url,
            "rarity": send.gift.rarity,
            "price_stars": send.gift.price_stars,
        } if send.gift else None,
        "sender": user_short(sender),
        "receiver": user_short(receiver),
    }
