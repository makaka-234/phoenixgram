"""Строковые константы-перечисления (хранятся как VARCHAR)."""


class ChatType:
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"

    ALL = {PRIVATE, GROUP, CHANNEL}


class MemberRole:
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

    ALL = {OWNER, ADMIN, MEMBER}


class MessageType:
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"
    STICKER = "sticker"
    SYSTEM = "system"
    GIFT = "gift"

    ALL = {TEXT, IMAGE, VIDEO, FILE, STICKER, SYSTEM, GIFT}


class ProductType:
    STARS = "stars"              # пакет Звёзд Феникс
    PREMIUM = "premium"          # подписка Феникс Премиум
    USERNAME = "username"        # красивый юзернейм
    VERIFICATION = "verification"  # верификация аккаунта

    ALL = {STARS, PREMIUM, USERNAME, VERIFICATION}


class OrderStatus:
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

    ALL = {PENDING, PAID, CANCELLED, REFUNDED}


class TransactionType:
    BONUS = "bonus"                  # бонус новому пользователю
    PURCHASE_IN = "purchase_in"      # покупка звёзд в приложении
    TRANSFER_IN = "transfer_in"      # перевод от другого пользователя
    TRANSFER_OUT = "transfer_out"    # перевод другому пользователю
    GIFT_IN = "gift_in"              # получен подарок
    GIFT_OUT = "gift_out"            # отправлен подарок
    ADMIN_CREDIT = "admin_credit"    # начисление админом
    ADMIN_DEBIT = "admin_debit"      # списание админом
    PREMIUM_SPEND = "premium_spend"  # покупка Premium за звёзды Феникс
    USERNAME_SPEND = "username_spend"
    VERIFICATION_SPEND = "verification_spend"

    ALL = {
        BONUS, PURCHASE_IN, TRANSFER_IN, TRANSFER_OUT, GIFT_IN, GIFT_OUT,
        ADMIN_CREDIT, ADMIN_DEBIT, PREMIUM_SPEND, USERNAME_SPEND, VERIFICATION_SPEND,
    }


class AdminRole:
    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"

    ALL = {OWNER, ADMIN, MODERATOR}
    LEVELS = {OWNER: 100, ADMIN: 50, MODERATOR: 10}
