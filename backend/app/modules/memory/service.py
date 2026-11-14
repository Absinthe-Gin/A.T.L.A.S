import logging
import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.memory.exceptions import ConversationNotFoundError
from app.modules.memory.models import MessageRole
from app.modules.memory.repository import (
    ConversationRepository,
    MemoryRepository,
    MessageRepository,
)
from app.modules.memory.schemas import ConversationData, MemoryData, MessageData

logger = logging.getLogger(__name__)

_TITLE_MAX_LENGTH = 80


def _title_from(text: str) -> str:
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    if len(first_line) <= _TITLE_MAX_LENGTH:
        return first_line
    return first_line[: _TITLE_MAX_LENGTH - 1].rstrip() + "…"


class ConversationService:
    """Conversation memory: conversations and their ordered messages."""

    def __init__(
        self,
        session: AsyncSession,
        conversations: ConversationRepository,
        messages: MessageRepository,
    ) -> None:
        self._session = session
        self._conversations = conversations
        self._messages = messages

    async def start_conversation(self, user_id: uuid.UUID, first_message: str) -> ConversationData:
        conversation = await self._conversations.add(user_id, _title_from(first_message) or None)
        await self._session.commit()
        logger.info("Conversation started", extra={"conversation_id": str(conversation.id)})
        return ConversationData.model_validate(conversation)

    async def get_conversation(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> ConversationData:
        """Return the conversation, or fail as if it did not exist when owned by someone else."""
        conversation = await self._conversations.get_for_user(conversation_id, user_id)
        if conversation is None:
            raise ConversationNotFoundError()
        return ConversationData.model_validate(conversation)

    async def append_message(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        *,
        tool_name: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> MessageData:
        """Store one message at the end of the conversation, in its own transaction."""
        sequence = await self._messages.next_sequence(conversation_id)
        message = await self._messages.add(
            conversation_id=conversation_id,
            sequence=sequence,
            role=role,
            content=content,
            tool_name=tool_name,
            meta=meta,
        )
        await self._session.commit()
        return MessageData.model_validate(message)

    async def list_recent_messages(
        self, conversation_id: uuid.UUID, limit: int
    ) -> list[MessageData]:
        """Return the last `limit` messages of this conversation only, oldest first."""
        messages = await self._messages.list_recent(conversation_id, limit)
        return [MessageData.model_validate(message) for message in messages]


# Words too common in Vietnamese and English to signal that a memory is relevant.
_STOP_WORDS = frozenset(
    {
        "anh", "bạn", "cho", "chị", "có", "của", "các", "cái", "em", "gì", "hãy", "không",
        "là", "làm", "mình", "một", "này", "nào", "những", "như", "thì", "tôi", "và", "với",
        "đi", "đó", "được", "để",
        "and", "are", "for", "the", "what", "with", "you",
    }
)  # fmt: skip
_WORD = re.compile(r"\w+")

# Only this many of the newest memories are considered for one request.
_CANDIDATE_LIMIT = 200


def _keywords(text: str) -> set[str]:
    return {
        word for word in _WORD.findall(text.lower()) if len(word) >= 2 and word not in _STOP_WORDS
    }


class MemoryService:
    """Long-term personal memory."""

    def __init__(self, memories: MemoryRepository) -> None:
        self._memories = memories

    async def find_relevant(self, user_id: uuid.UUID, query: str, limit: int) -> list[MemoryData]:
        """Return the user's memories that share keywords with `query`, best match first.

        Keyword overlap is the MVP strategy (no vector database). Memories with
        no overlap are never returned, so unrelated memories stay out of the context.
        """
        query_keywords = _keywords(query)
        if limit <= 0 or not query_keywords:
            return []

        candidates = await self._memories.list_recent_for_user(user_id, _CANDIDATE_LIMIT)
        scored = [
            (len(query_keywords & _keywords(memory.content)), memory) for memory in candidates
        ]
        # Stable sort keeps the repository's newest-first order within one score.
        relevant = sorted((item for item in scored if item[0] > 0), key=lambda item: -item[0])
        return [MemoryData.model_validate(memory) for _, memory in relevant[:limit]]
