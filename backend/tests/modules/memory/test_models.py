"""Database-level guarantees of the memory tables, checked on a migrated database."""

import uuid
from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError, InvalidRequestError, StatementError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.memory.models import (
    Conversation,
    Memory,
    MemoryCategory,
    MemorySource,
    Message,
    MessageRole,
)
from app.modules.users.models import DEFAULT_USER_ID, User


async def _conversation(session: AsyncSession, title: str | None = None) -> Conversation:
    conversation = Conversation(user_id=DEFAULT_USER_ID, title=title)
    session.add(conversation)
    await session.flush()
    return conversation


def _message(conversation: Conversation, sequence: int, content: str = "xin chào") -> Message:
    return Message(
        conversation_id=conversation.id,
        sequence=sequence,
        role=MessageRole.USER,
        content=content,
    )


async def test_default_user_exists(session: AsyncSession) -> None:
    user = await session.get(User, DEFAULT_USER_ID)

    assert user is not None
    assert user.display_name == "Người dùng"


async def test_ids_and_timestamps_are_generated(session: AsyncSession) -> None:
    before = datetime.now(UTC)

    conversation = await _conversation(session)
    await session.commit()

    assert isinstance(conversation.id, uuid.UUID)
    assert conversation.created_at >= before
    assert conversation.updated_at >= before
    assert conversation.title is None


async def test_timestamps_are_returned_in_utc(session: AsyncSession) -> None:
    conversation = await _conversation(session)
    await session.commit()
    conversation_id = conversation.id
    session.expire_all()

    loaded = await session.get(Conversation, conversation_id)

    assert loaded is not None
    assert loaded.created_at.tzinfo is UTC


async def test_timestamps_in_other_timezones_are_converted_to_utc(session: AsyncSession) -> None:
    hanoi = timezone(timedelta(hours=7))
    conversation = Conversation(
        user_id=DEFAULT_USER_ID, created_at=datetime(2026, 1, 1, 7, 0, tzinfo=hanoi)
    )
    session.add(conversation)
    await session.commit()
    conversation_id = conversation.id
    session.expire_all()

    loaded = await session.get(Conversation, conversation_id)

    assert loaded is not None
    assert loaded.created_at == datetime(2026, 1, 1, 0, 0, tzinfo=UTC)


async def test_naive_timestamps_are_rejected(session: AsyncSession) -> None:
    session.add(Conversation(user_id=DEFAULT_USER_ID, created_at=datetime(2026, 1, 1)))

    with pytest.raises(StatementError, match="Naive datetime"):
        await session.flush()


async def test_updated_at_changes_on_update(session: AsyncSession) -> None:
    conversation = await _conversation(session, title="Cũ")
    await session.commit()
    created_at, first_updated_at = conversation.created_at, conversation.updated_at

    conversation.title = "Mới"
    await session.commit()

    assert conversation.updated_at > first_updated_at
    assert conversation.created_at == created_at


async def test_conversation_requires_an_existing_user(session: AsyncSession) -> None:
    session.add(Conversation(user_id=uuid.uuid4()))

    with pytest.raises(IntegrityError):
        await session.flush()


async def test_user_with_conversations_cannot_be_deleted(session: AsyncSession) -> None:
    await _conversation(session)
    await session.commit()

    with pytest.raises(IntegrityError):
        await session.execute(delete(User).where(User.id == DEFAULT_USER_ID))


async def test_message_fields_round_trip(session: AsyncSession) -> None:
    conversation = await _conversation(session)
    message = Message(
        conversation_id=conversation.id,
        sequence=0,
        role=MessageRole.TOOL,
        content='{"total": 150000}',
        tool_name="finance_get_summary",
        meta={"duration_ms": 12, "status": "success", "nested": {"đơn_vị": "VND"}},
    )
    session.add(message)
    await session.commit()
    message_id = message.id
    session.expire_all()

    loaded = await session.get(Message, message_id)

    assert loaded is not None
    assert loaded.role is MessageRole.TOOL
    assert loaded.tool_name == "finance_get_summary"
    assert loaded.meta == {"duration_ms": 12, "status": "success", "nested": {"đơn_vị": "VND"}}


async def test_message_optional_fields_default_to_null(session: AsyncSession) -> None:
    conversation = await _conversation(session)
    message = _message(conversation, 0)
    session.add(message)
    await session.commit()

    assert message.tool_name is None
    assert message.meta is None


async def test_message_sequence_is_unique_within_a_conversation(session: AsyncSession) -> None:
    conversation = await _conversation(session)
    session.add_all([_message(conversation, 0), _message(conversation, 0)])

    with pytest.raises(IntegrityError):
        await session.flush()


async def test_same_sequence_is_allowed_in_different_conversations(session: AsyncSession) -> None:
    first = await _conversation(session)
    second = await _conversation(session)
    session.add_all([_message(first, 0), _message(second, 0)])

    await session.commit()

    assert await session.scalar(select(func.count()).select_from(Message)) == 2


async def test_negative_message_sequence_is_rejected(session: AsyncSession) -> None:
    conversation = await _conversation(session)
    session.add(_message(conversation, -1))

    with pytest.raises(IntegrityError):
        await session.flush()


async def test_message_requires_an_existing_conversation(session: AsyncSession) -> None:
    session.add(
        Message(conversation_id=uuid.uuid4(), sequence=0, role=MessageRole.USER, content="x")
    )

    with pytest.raises(IntegrityError):
        await session.flush()


async def test_unknown_message_role_is_rejected(session: AsyncSession) -> None:
    conversation = await _conversation(session)
    session.add(
        Message(
            conversation_id=conversation.id,
            sequence=0,
            role="moderator",
            content="x",
        )
    )

    with pytest.raises(StatementError):
        await session.flush()


async def test_messages_are_loaded_in_sequence_order(session: AsyncSession) -> None:
    conversation = await _conversation(session)
    session.add_all(
        [
            _message(conversation, 2, "ba"),
            _message(conversation, 0, "một"),
            _message(conversation, 1, "hai"),
        ]
    )
    await session.commit()
    conversation_id = conversation.id
    session.expire_all()

    loaded = await session.scalar(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )

    assert loaded is not None
    assert [message.content for message in loaded.messages] == ["một", "hai", "ba"]


async def test_messages_are_never_loaded_implicitly(session: AsyncSession) -> None:
    conversation = await _conversation(session)
    await session.commit()
    conversation_id = conversation.id
    session.expire_all()

    loaded = await session.get(Conversation, conversation_id)

    assert loaded is not None
    with pytest.raises(InvalidRequestError):
        _ = loaded.messages


async def test_deleting_a_conversation_deletes_only_its_messages(session: AsyncSession) -> None:
    doomed = await _conversation(session)
    kept = await _conversation(session)
    session.add_all([_message(doomed, 0), _message(doomed, 1), _message(kept, 0)])
    await session.commit()

    await session.execute(delete(Conversation).where(Conversation.id == doomed.id))
    await session.commit()

    remaining = (await session.scalars(select(Message.conversation_id))).all()
    assert remaining == [kept.id]


async def test_memory_fields_round_trip(session: AsyncSession) -> None:
    memory = Memory(
        user_id=DEFAULT_USER_ID,
        category=MemoryCategory.PREFERENCE,
        content="Thích ăn phở",
        source=MemorySource.USER_CONFIRMED,
    )
    session.add(memory)
    await session.commit()
    memory_id = memory.id
    session.expire_all()

    loaded = await session.get(Memory, memory_id)

    assert loaded is not None
    assert loaded.category is MemoryCategory.PREFERENCE
    assert loaded.source is MemorySource.USER_CONFIRMED
    assert loaded.content == "Thích ăn phở"
    assert loaded.source_message_id is None
    assert loaded.created_at.tzinfo is UTC


async def test_memory_requires_an_existing_user(session: AsyncSession) -> None:
    session.add(
        Memory(
            user_id=uuid.uuid4(),
            category=MemoryCategory.FACT,
            content="x",
            source=MemorySource.AI_INFERRED,
        )
    )

    with pytest.raises(IntegrityError):
        await session.flush()


async def test_memory_survives_deletion_of_its_source_conversation(session: AsyncSession) -> None:
    conversation = await _conversation(session)
    message = _message(conversation, 0, "Tôi thích cà phê sữa đá")
    session.add(message)
    await session.flush()
    memory = Memory(
        user_id=DEFAULT_USER_ID,
        category=MemoryCategory.PREFERENCE,
        content="Thích cà phê sữa đá",
        source=MemorySource.AI_INFERRED,
        source_message_id=message.id,
    )
    session.add(memory)
    await session.commit()

    await session.execute(delete(Conversation).where(Conversation.id == conversation.id))
    await session.commit()
    memory_id = memory.id
    session.expire_all()

    loaded = await session.get(Memory, memory_id)
    assert loaded is not None
    assert loaded.source_message_id is None
    assert loaded.content == "Thích cà phê sữa đá"
