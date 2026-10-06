import asyncio
import logging
from datetime import datetime, timedelta

import jwt
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import BigInteger, String, Integer, DateTime, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# ============ НАСТРОЙКИ ============
SECRET_KEY = "phoenixgram-secret-key-change-me"
ALGORITHM = "HS256"
TOKEN_EXPIRES_DAYS = 30
DB_URL = "sqlite+aiosqlite:///./phoenix_backend.db"

# ============ БАЗА ДАННЫХ ============
engine = create_async_engine(DB_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    phoenix_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    phoenix_stars: Mapped[int] = mapped_column(Integer, default=0)
    login_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    verified: Mapped[bool] = mapped_column(Integer, default=0)
    premium_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ============ СХЕМЫ ============
class LoginRequest(BaseModel):
    phoenix_id: str
    code: str

class LoginResponse(BaseModel):
    token: str
    user: dict

# ============ APP ============
app = FastAPI(
    title="PhoenixGram API",
    description="Backend для мессенджера PhoenixGram",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()
    print("✅ PhoenixGram Backend запущен!")

@app.get("/")
async def root():
    return {"app": "PhoenixGram API", "version": "1.0.0", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# ============ АВТОРИЗАЦИЯ ============
@app.post("/auth/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    """Вход по PhoenixGram ID и коду из Telegram-бота."""
    async with async_session() as session:
        user = (await session.execute(
            select(User).where(User.phoenix_id == data.phoenix_id.lower())
        )).scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        if user.login_code != data.code:
            raise HTTPException(status_code=401, detail="Неверный код")

        # Сбрасываем код после использования (одноразовый)
        user.login_code = None
        await session.commit()

        # Создаём JWT
        token = jwt.encode(
            {
                "user_id": user.id,
                "phoenix_id": user.phoenix_id,
                "exp": datetime.utcnow() + timedelta(days=TOKEN_EXPIRES_DAYS),
            },
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        return LoginResponse(
            token=token,
            user={
                "id": user.id,
                "phoenix_id": user.phoenix_id,
                "username": user.username,
                "phoenix_stars": user.phoenix_stars,
                "verified": bool(user.verified),
                "premium_until": user.premium_until.isoformat() if user.premium_until else None,
            },
        )

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Нет токена")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истёк")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Неверный токен")

    async with async_session() as session:
        user = (await session.execute(
            select(User).where(User.id == payload["user_id"])
        )).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        return user

@app.get("/users/me")
async def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "phoenix_id": user.phoenix_id,
        "username": user.username,
        "phoenix_stars": user.phoenix_stars,
        "verified": bool(user.verified),
        "premium_until": user.premium_until.isoformat() if user.premium_until else None,
        "created_at": user.created_at.isoformat(),
    }

# ============ РЕГИСТРАЦИЯ ЮЗЕРА (для теста) ============
@app.post("/internal/register")
async def register(data: dict):
    """Создаёт или обновляет юзера. Используется ботом."""
    phoenix_id = data.get("phoenix_id", "").lower()
    code = data.get("code")
    if not phoenix_id or not code:
        raise HTTPException(status_code=400, detail="phoenix_id и code обязательны")

    async with async_session() as session:
        user = (await session.execute(
            select(User).where(User.phoenix_id == phoenix_id)
        )).scalar_one_or_none()

        if user:
            user.login_code = code
        else:
            user = User(
                phoenix_id=phoenix_id,
                username=data.get("username"),
                phoenix_stars=1000,
                login_code=code,
            )
            session.add(user)

        await session.commit()
        return {"ok": True, "phoenix_id": phoenix_id}


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)

