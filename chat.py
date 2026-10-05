"""Схемы чатов."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel
from app.schemas.user import UserShort


class ChatCreate(BaseModel):
    type: str = Field("private", pattern="^(private|group|channel)$")
    title: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = Field(None, max_length=512)
    member_ids: List[int] = Field(default_factory=list)
    peer_phoenix_id: Optional[str] = None  # для личного чата


class ChatUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = Field(None, max_length=512)
    avatar_url: Optional[str] = Field(None, max_length=512)


class ChatMemberOut(ORMModel):
    id: int
    user_id: int
    role: str
    is_muted: bool = False
    last_read_message_id: Optional[int] = None
    joined_at: Optional[datetime] = None


class ChatOut(ORMModel):
    id: int
    type: str
    title: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
    owner_id: Optional[int] = None
    last_message_id: Optional[int] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime


class ChatDetail(ChatOut):
    members: List[ChatMemberOut] = Field(default_factory=list)
    peer: Optional[UserShort] = None  # собеседник в личном чате
    unread_count: int = 0


class ChatListOut(ChatOut):
    peer: Optional[UserShort] = None
    last_message_text: Optional[str] = None
    unread_count: int = 0
