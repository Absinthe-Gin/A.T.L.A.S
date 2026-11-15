import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base, TimestampMixin, UtcDateTime, UuidPrimaryKeyMixin


class PendingActionStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    # Confirmed by the user, but the module refused it (for example a deleted category).
    FAILED = "failed"


class PendingAction(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """A change the assistant proposed. It runs only after the user confirms it."""

    __tablename__ = "ai_pending_actions"
    __table_args__ = (Index("ix_ai_pending_actions_user_id_status", "user_id", "status"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    # A proposal belongs to its conversation and goes with it.
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Validated tool input; validated again before it runs.
    arguments: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[PendingActionStatus] = mapped_column(
        Enum(
            PendingActionStatus,
            native_enum=False,
            create_constraint=False,
            length=20,
            values_callable=lambda members: [member.value for member in members],
            validate_strings=True,
        ),
        nullable=False,
        default=PendingActionStatus.PENDING,
    )
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error_code: Mapped[str | None] = mapped_column(String(100))
    error_message: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
