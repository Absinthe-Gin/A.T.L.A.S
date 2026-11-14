from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import (
    Base,
    CreatedAtMixin,
    TimestampMixin,
    UuidPrimaryKeyMixin,
)


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


class MemoryCategory(StrEnum):
    PREFERENCE = "preference"
    HABIT = "habit"
    GOAL = "goal"
    FACT = "fact"


class MemorySource(StrEnum):
    """Who vouches for a memory: the user, or an inference made by the AI."""

    USER_CONFIRMED = "user_confirmed"
    AI_INFERRED = "ai_inferred"


def _string_enum(enum_class: type[StrEnum], length: int) -> Enum:
    """Store an enum as a plain string so the schema is portable across databases.

    Allowed values are validated by the application, not by a database constraint,
    so adding a value does not require rebuilding the table.
    """
    return Enum(
        enum_class,
        native_enum=False,
        create_constraint=False,
        length=length,
        values_callable=lambda members: [member.value for member in members],
        validate_strings=True,
    )


class Conversation(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """One chat session between the user and the assistant."""

    __tablename__ = "conversations"
    __table_args__ = (Index("ix_conversations_user_id_updated_at", "user_id", "updated_at"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(200))

    # Never loaded implicitly: async code must request messages explicitly.
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        order_by="Message.sequence",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )


class Message(UuidPrimaryKeyMixin, CreatedAtMixin, Base):
    """One message, or one tool execution record, inside a conversation."""

    __tablename__ = "messages"
    __table_args__ = (
        # Also serves as the index for loading history in order.
        UniqueConstraint("conversation_id", "sequence"),
        CheckConstraint("sequence >= 0", name="sequence_non_negative"),
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    # Position inside the conversation; timestamps can collide within one turn.
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[MessageRole] = mapped_column(_string_enum(MessageRole, 20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(100))
    # `metadata` is reserved by SQLAlchemy on model classes, hence `meta`.
    meta: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON)

    conversation: Mapped[Conversation] = relationship(back_populates="messages", lazy="raise")


class Memory(UuidPrimaryKeyMixin, TimestampMixin, Base):
    """A long-lived fact about the user that is useful in later conversations."""

    __tablename__ = "memories"
    __table_args__ = (Index("ix_memories_user_id_category", "user_id", "category"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    category: Mapped[MemoryCategory] = mapped_column(
        _string_enum(MemoryCategory, 50), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[MemorySource] = mapped_column(_string_enum(MemorySource, 20), nullable=False)
    # Deleting a conversation must not delete what was learned from it.
    source_message_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("messages.id", ondelete="SET NULL")
    )
