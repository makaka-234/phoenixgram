"""Сервис подарков."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commerce import Gift, GiftSend, Transaction
from app.models.enums import MessageType, TransactionType
from app.models.user import User
from app.services.chat_service import create_private_chat
from app.services.message_service import create_message
from app.services.star_service import StarError, change_balance


class GiftError(Exception):
    pass


async def list_catalog(db: AsyncSession, only_active: bool = True) -> list[Gift]:
    stmt = select(Gift)
    if only_active:
        stmt = stmt.where(Gift.is_active.is_(True))
    stmt = stmt.order_by(Gift.sort_order.asc(), Gift.price_stars.asc())
    return list((await db.execute(stmt)).scalars().all())


async def send_gift(
    db: AsyncSession,
    sender: User,
    gift_id: int,
    receiver_phoenix_id: str,
    message: str | None = None,
    is_anonymous: bool = False,
) -> GiftSend:
    gift = await db.get(Gift, gift_id)
    if gift is None or not gift.is_active:
        raise GiftError("Подарок недоступен")

    receiver = (
        await db.execute(
            select(User).where(func.lower(User.phoenix_id) == receiver_phoenix_id.lower())
        )
    ).scalar_one_or_none()
    if receiver is None:
        raise GiftError("Получатель не найден")
    if receiver.id == sender.id:
        raise GiftError("Нельзя отправить подарок самому себе")
    if receiver.is_banned:
        raise GiftError("Получатель заблокирован")

    # Списываем звёзды у отправителя.
    try:
        await change_balance(
            db,
            sender.id,
            -gift.price_stars,
            TransactionType.GIFT_OUT,
            f"Подарок «{gift.title}» для @{receiver.phoenix_id}",
            related_user_id=receiver.id,
            commit=False,
        )
    except StarError as exc:
        await db.rollback()
        raise GiftError(str(exc))

    send = GiftSend(
        gift_id=gift.id,
        sender_id=sender.id,
        receiver_id=receiver.id,
        price_paid=gift.price_stars,
        message=message,
        is_anonymous=is_anonymous,
    )
    db.add(send)
    await db.flush()

    # Начисляем «стоимость» подарка получателю как звёзды? Нет —
    # подарок не обменивается на звёзды, но фиксируем транзакцию получения (0 баланс-эффект).
    tx = Transaction(
        user_id=receiver.id,
        amount=0,
        balance_after=receiver.stars_balance,
        type=TransactionType.GIFT_IN,
        description=f"Подарок «{gift.title}»" + ("" if is_anonymous else f" от @{sender.phoenix_id}"),
        related_user_id=sender.id,
        gift_send_id=send.id,
    )
    db.add(tx)

    # Личный чат между отправителем и получателем + сообщение-подарок.
    chat = await create_private_chat(db, sender, receiver.phoenix_id)
    await create_message(
        db,
        chat_id=chat.id,
        sender_id=sender.id,
        msg_type=MessageType.GIFT,
        media_meta={
            "gift_id": gift.id,
            "gift_send_id": send.id,
            "title": gift.title,
            "emoji": gift.emoji,
            "image_url": gift.image_url,
            "message": message,
            "anonymous": is_anonymous,
        },
    )

    await db.commit()
    await db.refresh(send)
    return send


async def list_sent(db: AsyncSession, user_id: int, limit: int = 50) -> list[GiftSend]:
    stmt = (
        select(GiftSend)
        .where(GiftSend.sender_id == user_id)
        .order_by(GiftSend.created_at.desc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_received(db: AsyncSession, user_id: int, limit: int = 50) -> list[GiftSend]:
    stmt = (
        select(GiftSend)
        .where(GiftSend.receiver_id == user_id)
        .order_by(GiftSend.created_at.desc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())
