"""Конфигурация приложения PhoenixGram (backend)."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Общее ---
    APP_NAME: str = "PhoenixGram"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # --- JWT ---
    SECRET_KEY: str = "change_me_to_a_long_random_string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- Инфраструктура ---
    DATABASE_URL: str = "postgresql+asyncpg://phoenix:phoenix@localhost:5432/phoenixgram"
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- CORS ---
    CORS_ORIGINS: str = "*"

    # --- Бизнес-правила ---
    NEW_USER_BONUS: int = 1000
    REG_CODE_TTL_MINUTES: int = 15

    # --- Telegram ---
    BOT_TOKEN: str = ""
    OWNER_TG_ID: int = 0
    BACKEND_URL: str = "http://localhost:8000"

    # --- Владелец админки (сидируется при старте) ---
    ADMIN_USERNAME: str = "owner"
    ADMIN_PASSWORD: str = "owner_secret_change_me"

    @property
    def cors_origins_list(self) -> List[str]:
        items = [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return items or ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
