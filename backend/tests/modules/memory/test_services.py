"""Repositories and services of the memory module, on a real database."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.memory.exceptions import ConversationNotFoundError
from app.modules.memory.models import Memory, MemoryCategory, MemorySource, MessageRole
from app.modules.memory.repository import (
    ConversationRepository,
    MemoryRepository,
    MessageRepository,
)
from app.modules.memory.service import ConversationService, MemoryService
from app.modules.users.models import DEFAULT_USER_ID, User
from app.modules.users.repository import UserRepository
from app.modules.users.service import DefaultUserMissingError, UserService


@pytest.fixture
def conversations(session: AsyncSession) -> ConversationService:
    return ConversationService(session, ConversationRepository(session), MessageRepository(session))


@pytest.fixture
def memories(session: AsyncSession) -> MemoryService:
    return MemoryService(MemoryRepository(session))


async def _add_memory(
    session: AsyncSession, content: str, user_id: uuid.UUID = DEFAULT_USER_ID
) -> Memory:
    memory = Memory(
        user_id=user_id,
        category=MemoryCategory.PREFERENCE,
        content=content,
        source=MemorySource.USER_CONFIRMED,
    )
    session.add(memory)
    await session.commit()
    return memory


# --- Conversations ----------------------------------------------------------


async def test_start_conversation_uses_the_first_message_as_title(
    conversations: ConversationService,
) -> None:
    conversation = await conversations.start_conversation(
        DEFAULT_USER_ID, "  Lên kế hoạch Đà Lạt\n"
    )

    assert conversation.title == "Lên kế hoạch Đà Lạt"
    assert conversation.user_id == DEFAULT_USER_ID


async def test_long_first_message_is_shortened_for_the_title(
    conversations: ConversationService,
) -> None:
    conversation = await conversations.start_conversation(DEFAULT_USER_ID, "a" * 300)

    assert conversation.title is not None
    assert len(conversation.title) == 80
    assert conversation.title.endswith("…")


async def test_only_the_first_line_becomes_the_title(conversations: ConversationService) -> None:
    conversation = await conversations.start_conversation(DEFAULT_USER_ID, "Dòng một\nDòng hai")

    assert conversation.title == "Dòng một"


async def test_get_conversation_returns_the_owners_conversation(
    conversations: ConversationService,
) -> None:
    created = await conversations.start_conversation(DEFAULT_USER_ID, "Chào")

    loaded = await conversations.get_conversation(created.id, DEFAULT_USER_ID)

    assert loaded.id == created.id


async def test_get_conversation_rejects_unknown_and_foreign_conversations(
    conversations: ConversationService, session: AsyncSession
) -> None:
    other = User(display_name="Người khác")
    session.add(other)
    await session.commit()
    created = await conversations.start_conversation(DEFAULT_USER_ID, "Chào")

    with pytest.raises(ConversationNotFoundError):
        await conversations.get_conversation(uuid.uuid4(), DEFAULT_USER_ID)
    with pytest.raises(ConversationNotFoundError):
        await conversations.get_conversation(created.id, other.id)


async def test_messages_are_numbered_in_the_order_they_are_appended(
    conversations: ConversationService,
) -> None:
    conversation = await conversations.start_conversation(DEFAULT_USER_ID, "Chào")

    first = await conversations.append_message(conversation.id, MessageRole.USER, "một")
    second = await conversations.append_message(
        conversation.id,
        MessageRole.TOOL,
        "{}",
        tool_name="demo_echo",
        meta={"status": "success"},
    )

    assert (first.sequence, second.sequence) == (0, 1)
    assert second.tool_name == "demo_echo"
    assert second.meta == {"status": "success"}


async def test_message_numbering_is_independent_per_conversation(
    conversations: ConversationService,
) -> None:
    first = await conversations.start_conversation(DEFAULT_USER_ID, "A")
    second = await conversations.start_conversation(DEFAULT_USER_ID, "B")
    await conversations.append_message(first.id, MessageRole.USER, "a0")
    await conversations.append_message(first.id, MessageRole.USER, "a1")

    message = await conversations.append_message(second.id, MessageRole.USER, "b0")

    assert message.sequence == 0


async def test_recent_messages_are_the_last_ones_oldest_first(
    conversations: ConversationService,
) -> None:
    conversation = await conversations.start_conversation(DEFAULT_USER_ID, "Chào")
    for text in ["một", "hai", "ba", "bốn"]:
        await conversations.append_message(conversation.id, MessageRole.USER, text)

    recent = await conversations.list_recent_messages(conversation.id, limit=2)

    assert [message.content for message in recent] == ["ba", "bốn"]


@pytest.mark.parametrize("limit", [0, -1])
async def test_recent_messages_with_a_non_positive_limit_is_empty(
    conversations: ConversationService, limit: int
) -> None:
    conversation = await conversations.start_conversation(DEFAULT_USER_ID, "Chào")
    await conversations.append_message(conversation.id, MessageRole.USER, "một")

    assert await conversations.list_recent_messages(conversation.id, limit=limit) == []


async def test_recent_messages_never_include_other_conversations(
    conversations: ConversationService,
) -> None:
    first = await conversations.start_conversation(DEFAULT_USER_ID, "A")
    second = await conversations.start_conversation(DEFAULT_USER_ID, "B")
    await conversations.append_message(first.id, MessageRole.USER, "của A")
    await conversations.append_message(second.id, MessageRole.USER, "của B")

    recent = await conversations.list_recent_messages(first.id, limit=10)

    assert [message.content for message in recent] == ["của A"]


async def test_recent_messages_of_an_unknown_conversation_is_empty(
    conversations: ConversationService,
) -> None:
    assert await conversations.list_recent_messages(uuid.uuid4(), limit=10) == []


# --- Memory retrieval -------------------------------------------------------


async def test_memories_sharing_keywords_with_the_query_are_returned(
    memories: MemoryService, session: AsyncSession
) -> None:
    await _add_memory(session, "Thích ăn phở bò")
    await _add_memory(session, "Đang học tiếng Nhật")

    found = await memories.find_relevant(DEFAULT_USER_ID, "Trưa nay ăn phở ở đâu?", limit=5)

    assert [memory.content for memory in found] == ["Thích ăn phở bò"]
    assert found[0].source is MemorySource.USER_CONFIRMED


async def test_better_matches_come_first(memories: MemoryService, session: AsyncSession) -> None:
    await _add_memory(session, "Thích cà phê")
    await _add_memory(session, "Thích cà phê sữa đá buổi sáng")

    found = await memories.find_relevant(DEFAULT_USER_ID, "cà phê sữa đá", limit=5)

    assert [memory.content for memory in found] == [
        "Thích cà phê sữa đá buổi sáng",
        "Thích cà phê",
    ]


async def test_memory_matching_ignores_case_and_common_words(
    memories: MemoryService, session: AsyncSession
) -> None:
    await _add_memory(session, "Tôi là người thích PHỞ")
    await _add_memory(session, "Tôi là lập trình viên")

    found = await memories.find_relevant(DEFAULT_USER_ID, "tôi là ai mà thích phở", limit=5)

    assert [memory.content for memory in found] == ["Tôi là người thích PHỞ"]


async def test_memory_results_respect_the_limit(
    memories: MemoryService, session: AsyncSession
) -> None:
    for index in range(4):
        await _add_memory(session, f"Thích phở số {index}")

    assert len(await memories.find_relevant(DEFAULT_USER_ID, "phở", limit=2)) == 2
    assert await memories.find_relevant(DEFAULT_USER_ID, "phở", limit=0) == []


@pytest.mark.parametrize("query", ["", "   ", "?!", "tôi là"])
async def test_query_without_keywords_returns_no_memories(
    memories: MemoryService, session: AsyncSession, query: str
) -> None:
    await _add_memory(session, "Tôi là người thích phở")

    assert await memories.find_relevant(DEFAULT_USER_ID, query, limit=5) == []


async def test_memories_of_other_users_are_never_returned(
    memories: MemoryService, session: AsyncSession
) -> None:
    other = User(display_name="Người khác")
    session.add(other)
    await session.commit()
    await _add_memory(session, "Thích phở", user_id=other.id)

    assert await memories.find_relevant(DEFAULT_USER_ID, "phở", limit=5) == []


# --- Users ------------------------------------------------------------------


async def test_current_user_is_the_default_local_user(session: AsyncSession) -> None:
    user = await UserService(UserRepository(session)).get_current_user()

    assert user.id == DEFAULT_USER_ID
    assert user.display_name == "Người dùng"


async def test_missing_default_user_is_reported_clearly(session: AsyncSession) -> None:
    await session.delete(await session.get(User, DEFAULT_USER_ID))
    await session.commit()

    with pytest.raises(DefaultUserMissingError, match="alembic upgrade head"):
        await UserService(UserRepository(session)).get_current_user()
