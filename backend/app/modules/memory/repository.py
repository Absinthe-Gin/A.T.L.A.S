import uuid
from collections.abc import Sequence
from datetime import datetime
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

    async def list_for_user(
        self, user_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[tuple[Conversation, datetime | None]]:
        """Conversations with the time of their last message, most recently active first."""
        last = (
            select(
                Message.conversation_id,
                func.max(Message.created_at).label("last_message_at"),
            )
            .group_by(Message.conversation_id)
            .subquery()
        )
        activity = func.coalesce(last.c.last_message_at, Conversation.created_at)
        statement = (
            select(Conversation, last.c.last_message_at)
            .outerjoin(last, last.c.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id)
            .order_by(activity.desc(), Conversation.id)
            .limit(limit)
            .offset(offset)
        )
        return [(row[0], row[1]) for row in (await self._session.execute(statement)).all()]

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        statement = (
            select(func.count()).select_from(Conversation).where(Conversation.user_id == user_id)
        )
        return int(await self._session.scalar(statement) or 0)

    async def last_message_at(self, conversation_id: uuid.UUID) -> datetime | None:
        statement = select(func.max(Message.created_at)).where(
            Message.conversation_id == conversation_id
        )
        return await self._session.scalar(statement)

    async def delete(self, conversation: Conversation) -> None:
        """Messages and pending actions go with it (database `ON DELETE CASCADE`)."""
        await self._session.delete(conversation)
        await self._session.flush()


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

    def _visible(self, conversation_id: uuid.UUID) -> Any:
        """What a person reads: their messages, the assistant's replies and system notes.

        Tool results and the assistant's empty tool-calling turns are internal steps.
        """
        return (
            Message.conversation_id == conversation_id,
            Message.role.in_([MessageRole.USER, MessageRole.ASSISTANT, MessageRole.SYSTEM]),
            Message.content != "",
        )

    async def list_visible(
        self, conversation_id: uuid.UUID, *, limit: int, offset: int
    ) -> Sequence[Message]:
        """Visible messages, newest first, so the first page is the latest part."""
        statement = (
            select(Message)
            .where(*self._visible(conversation_id))
            .order_by(Message.sequence.desc())
            .limit(limit)
            .offset(offset)
        )
        return (await self._session.scalars(statement)).all()

    async def count_visible(self, conversation_id: uuid.UUID) -> int:
        statement = select(func.count()).select_from(Message).where(*self._visible(conversation_id))
        return int(await self._session.scalar(statement) or 0)


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
