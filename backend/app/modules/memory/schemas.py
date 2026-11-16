"""Data the memory module hands to other modules. ORM models never leave the module."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.memory.models import MemoryCategory, MemorySource, MessageRole


class ConversationData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class MessageData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    sequence: int
    role: MessageRole
    content: str
    tool_name: str | None
    meta: dict[str, Any] | None
    created_at: datetime


class ConversationSummary(BaseModel):
    """One entry of the conversation list."""

    id: uuid.UUID
    title: str | None
    created_at: datetime
    last_message_at: datetime


class ConversationMessage(BaseModel):
    """A message as the person reads it. Internal tool steps are not included."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime


class ConversationRename(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Tên cuộc trò chuyện không được để trống.")
        return stripped


class MemoryData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: MemoryCategory
    content: str
    source: MemorySource
    created_at: datetime
