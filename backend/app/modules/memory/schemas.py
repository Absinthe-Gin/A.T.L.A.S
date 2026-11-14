"""Data the memory module hands to other modules. ORM models never leave the module."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

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


class MemoryData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: MemoryCategory
    content: str
    source: MemorySource
    created_at: datetime
