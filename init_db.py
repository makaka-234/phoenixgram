"""Инициализация БД: создание таблиц и первичных данных.

Запуск:  python -m app.init_db
"""
from __future__ import annotations

import asyncio
import json
import logging

from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models import Admin, Base, Gift, Product
from app.models.enums import AdminRole, ProductType

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("phoenixgram.init")


DEFAULT_PRODUCTS = [
    # --- Пакеты Звёзд Феникс (цена в Telegram Stars) ---
    dict(code="stars_100", title="100 Звёзд Феникс", type=ProductType.STARS,
         price_xtr=50, phoenix_stars=100, emoji="⭐", sort_order=10,
         description="Небольшой пакет Звёзд Феникс для подарков и Premium."),
    dict(code="stars_500", title="500 Звёзд Феникс", type=ProductType.STARS,
         price_xtr=200, phoenix_stars=500, emoji="🌟", sort_order=20,
         description="Оптимальный пакет. Выгоднее на 20%."),
    dict(code="stars_1000", title="1000 Звёзд Феникс", type=ProductType.STARS,
         price_xtr=350, phoenix_stars=1000, emoji="💫", sort_order=30,
         description="Максимальный пакет. Лучшая цена за звезду."),
    # --- Феникс Премиум ---
    dict(code="premium_1m", title="Феникс Премиум — 1 месяц", type=ProductType.PREMIUM,
         price_xtr=250, premium_days=30, emoji="👑", sort_order=40,
         description="Подписка на 30 дней: значок Premium, расширенные лимиты."),
    dict(code="premium_3m", title="Феникс Премиум — 3 месяца", type=ProductType.PREMIUM,
         price_xtr=650, premium_days=90, emoji="👑", sort_order=50,
         description="Подписка на 90 дней со скидкой."),
    dict(code="premium_12m", title="Феникс Премиум — 12 месяцев", type=ProductType.PREMIUM,
         price_xtr=2400, premium_days=365, emoji="👑", sort_order=60,
         description="Годовая подписка. Максимальная выгода."),
    # --- Красивые юзернеймы ---
    dict(code="username_short", title="Красивый юзернейм (4–5 символов)", type=ProductType.USERNAME,
         price_xtr=500, emoji="🔤", sort_order=70,
         description="Короткий и запоминающийся @username.", payload={"username": ""}),
    dict(code="username_elite", title="Элитный юзернейм (3 символа)", type=ProductType.USERNAME,
         price_xtr=1500, emoji="✒️", sort_order=80,
         description="Максимально короткий юзернейм.", payload={"username": ""}),
    # --- Верификация ---
    dict(code="verification", title="Верификация аккаунта", type=ProductType.VERIFICATION,
         price_xtr=1200, emoji="☑️", sort_order=90,
         description="Синяя галочка рядом с вашим PhoenixGram ID."),
]

DEFAULT_GIFTS = [
    dict(code="rose", title="Роза", emoji="🌹", price_stars=10, rarity="common", sort_order=10,
         description="Классический подарок."),
    dict(code="heart", title="Сердце", emoji="❤️", price_stars=25, rarity="common", sort_order=20,
         description="Простое признание в симпатии."),
    dict(code="star", title="Звезда", emoji="⭐", price_stars=50, rarity="rare", sort_order=30,
         description="Сияющий подарок."),
    dict(code="cake", title="Торт", emoji="🎂", price_stars=75, rarity="rare", sort_order=40,
         description="С днём рождения!"),
    dict(code="rocket", title="Ракета", emoji="🚀", price_stars=150, rarity="epic", sort_order=50,
         description="Для самых амбициозных."),
    dict(code="crown", title="Корона", emoji="👑", price_stars=300, rarity="epic", sort_order=60,
         description="Покажите, кто здесь royalty."),
    dict(code="phoenix", title="Феникс", emoji="🐦‍🔥", price_stars=1000, rarity="legendary", sort_order=70,
         description="Легендарный подарок PhoenixGram."),
]


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы созданы/проверены")


async def seed_products() -> None:
    async with AsyncSessionLocal() as db:
        for item in DEFAULT_PRODUCTS:
            existing = (
                await db.execute(select(Product).where(Product.code == item["code"]))
            ).scalar_one_or_none()
            if existing is not None:
                continue
            payload = item.get("payload")
            db.add(Product(
                code=item["code"],
                title=item["title"],
                description=item.get("description"),
                type=item["type"],
                price_xtr=item.get("price_xtr", 0),
                phoenix_stars=item.get("phoenix_stars", 0),
                premium_days=item.get("premium_days", 0),
                emoji=item.get("emoji", "⭐"),
                sort_order=item.get("sort_order", 0),
                payload=json.dumps(payload, ensure_ascii=False) if payload else None,
                is_active=True,
            ))
        await db.commit()
    logger.info("Товары просидированы")


async def seed_gifts() -> None:
    async with AsyncSessionLocal() as db:
        for item in DEFAULT_GIFTS:
            existing = (
                await db.execute(select(Gift).where(Gift.code == item["code"]))
            ).scalar_one_or_none()
            if existing is not None:
                continue
            db.add(Gift(**item, is_active=True))
        await db.commit()
    logger.info("Подарки просидированы")


async def seed_owner() -> None:
    async with AsyncSessionLocal() as db:
        count = int((await db.execute(select(func.count(Admin.id)))).scalar() or 0)
        if count > 0:
            logger.info("Администраторы уже есть — пропускаем создание владельца")
            return
        owner = Admin(
            username=settings.ADMIN_USERNAME,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role=AdminRole.OWNER,
            tg_id=settings.OWNER_TG_ID or None,
            is_active=True,
        )
        db.add(owner)
        await db.commit()
        logger.info("Создан владелец админки: %s", settings.ADMIN_USERNAME)


async def main() -> None:
    await create_tables()
    await seed_products()
    await seed_gifts()
    await seed_owner()
    await engine.dispose()
    logger.info("Инициализация завершена ✔")


if __name__ == "__main__":
    asyncio.run(main())
