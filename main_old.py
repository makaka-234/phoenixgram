"""PhoenixGram backend — точка входа FastAPI."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.core.config import settings
from app.core.database import engine
from app.core.redis_client import close_redis, init_redis
from app.models import Base
from app.routers import api_router
from app.ws.manager import manager

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("phoenixgram")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Таблицы (в проде лучше Alembic, но create_all идемпотентен).
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы БД готовы")

    # 2. Redis + ws consumer.
    await init_redis()
    manager.start_consumer()
    logger.info("Redis инициализирован")

    yield

    await manager.stop_consumer()
    await close_redis()
    await engine.dispose()
    logger.info("PhoenixGram backend остановлен")


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description=(
        "API мессенджера PhoenixGram.\n\n"
        "**Звёзды Феникс** — внутренняя валюта, вывод средств невозможен. "
        "Покупка осуществляется только за Telegram Stars (XTR)."
    ),
    version="1.0.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Служебное"], summary="Корень API")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "api": settings.API_V1_PREFIX,
        "note": "Звёзды Феникс — внутренняя валюта. Вывод невозможен.",
    }


@app.get("/health", tags=["Служебное"], summary="Проверка работоспособности")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
