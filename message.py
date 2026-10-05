"""Схемы сообщений."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel
from app.schemas.user import UserShort


class MessageCreate(BaseModel):
    text: Optional[str] = Field(None, max_length=4096)
    type: str = "text"
    media_url: Optional[str] = Field(None, max_length=512)
    media_meta: Optional[dict] = None
    reply_to_id: Optional[int] = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() == "":
            return None
        return v


class MessageOut(ORMModel):
    id: int
    chat_id: int
    sender_id: Optional[int] = None
    type: str
    text: Optional[str] = None
    media_url: Optional[str] = None
    reply_to_id: Optional[int] = None
    is_edited: bool = False
    is_deleted: bool = False
    created_at: datetime
    edited_at: Optional[datetime] = None
    sender: Optional[UserShort] = None


class MessagePage(BaseModel):
    items: list[MessageOut]
    has_more: bool
    next_before_id: Optional[int] = None


class WSIncoming(BaseModel):
    """Входящее WebSocket-сообщение от клиента."""
    action: str  # send | typing | read | ping
    chat_id: Optional[int] = None
    data: Optional[dict] = None


class WSOutgoing(BaseModel):
    """Исходящее WebSocket-сообщение клиенту."""
    event: str  # message | typing | read | presence | error | pong
    chat_id: Optional[int] = None
    payload: Optional[dict] = None
