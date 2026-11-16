import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.shared.tools import ToolStatus


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    # Omit to start a new conversation.
    conversation_id: uuid.UUID | None = None

    @field_validator("message")
    @classmethod
    def _message_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Tin nhắn không được để trống.")
        return value.strip()


class ToolCallSummary(BaseModel):
    name: str
    status: ToolStatus


class PendingActionView(BaseModel):
    """A change the assistant proposed; the user confirms or cancels it."""

    id: uuid.UUID
    tool_name: str
    summary: str
    status: str
    error_message: str | None = None
    created_at: datetime | None = None


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    # ID of the assistant message that carries `reply`.
    message_id: uuid.UUID
    reply: str
    intent: str
    tool_calls: list[ToolCallSummary]
    pending_actions: list[PendingActionView] = []
