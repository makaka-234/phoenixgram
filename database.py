"""Асинхронное подключение к PostgreSQL (SQLAlchemy 2.x)."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

_engine_kwargs: dict = {"echo": settings.DEBUG, "pool_pre_ping": True}
# SQLite (используется только в тестах) не поддерживает pooling-параметры.
if not settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update({"pool_size": 10, "max_overflow": 20})

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI-зависимость: сессия БД на время запроса."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
