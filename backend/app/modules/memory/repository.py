import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.memory.models import Conversation, Memory, Message, MessageRole


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user_id: uuid.UUID, title: str | None) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self._session.add(conversation)
        await self._session.flush()
        return conversation

    async def get_for_user(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> Conversation | None:
        """Return the conversation only if it belongs to `user_id`."""
        statement = select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
        return await self._session.scalar(statement)


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def next_sequence(self, conversation_id: uuid.UUID) -> int:
        statement = select(func.max(Message.sequence)).where(
            Message.conversation_id == conversation_id
        )
        last = await self._session.scalar(statement)
        return 0 if last is None else last + 1

    async def add(
        self,
        *,
        conversation_id: uuid.UUID,
        sequence: int,
        role: MessageRole,
        content: str,
        tool_name: str | None,
        meta: dict[str, Any] | None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            sequence=sequence,
            role=role,
            content=content,
            tool_name=tool_name,
            meta=meta,
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def list_recent(self, conversation_id: uuid.UUID, limit: int) -> Sequence[Message]:
        """Return the last `limit` messages of one conversation, oldest first."""
        if limit <= 0:
            return []
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence.desc())
            .limit(limit)
        )
        newest_first = (await self._session.scalars(statement)).all()
        return list(reversed(newest_first))


class MemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_recent_for_user(self, user_id: uuid.UUID, limit: int) -> Sequence[Memory]:
        statement = (
            select(Memory)
            .where(Memory.user_id == user_id)
            .order_by(Memory.updated_at.desc())
            .limit(limit)
        )
        return (await self._session.scalars(statement)).all()
