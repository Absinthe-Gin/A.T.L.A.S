"""Write tools only propose; the change happens after the user confirms (CLAUDE.md 6.2)."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.actions import (
    PendingActionNotFoundError,
    PendingActionResolvedError,
    PendingActionService,
)
from app.modules.ai.models import PendingAction, PendingActionStatus
from app.modules.ai.orchestrator import Orchestrator
from app.modules.ai.providers.mock import MockLLMProvider
from app.modules.memory.models import Message, MessageRole
from app.modules.memory.repository import (
    ConversationRepository,
    MemoryRepository,
    MessageRepository,
)
from app.modules.memory.service import ConversationService, MemoryService
from app.modules.users.models import DEFAULT_USER_ID, User
from app.shared.tools import ToolStatus
from tests.ai_support import SaveNoteTool, build_actions, build_runtime, tool_call

DEMO_INTENT = '{"intent": "demo"}'


def _setup(
    session: AsyncSession, script: list[object]
) -> tuple[Orchestrator, PendingActionService, SaveNoteTool, MockLLMProvider]:
    tool = SaveNoteTool()
    provider = MockLLMProvider(script)  # type: ignore[arg-type]
    runtime = build_runtime(provider, [tool])
    actions = build_actions(session, runtime)
    orchestrator = Orchestrator(
        provider=runtime.provider,
        intent_classifier=runtime.intent_classifier,
        registry=runtime.registry,
        executor=runtime.executor,
        conversations=ConversationService(
            session, ConversationRepository(session), MessageRepository(session)
        ),
        memories=MemoryService(MemoryRepository(session)),
        actions=actions,
        limits=runtime.limits,
    )
    return orchestrator, actions, tool, provider


async def _propose(
    session: AsyncSession, text: str = "mua sữa"
) -> tuple[uuid.UUID, PendingActionService, SaveNoteTool]:
    orchestrator, actions, tool, _ = _setup(
        session, [DEMO_INTENT, [tool_call("demo_save_note", text=text)], "Bạn xác nhận nhé."]
    )
    result = await orchestrator.handle(
        user_id=DEFAULT_USER_ID, text="Ghi chú giúp mình", conversation_id=None
    )
    return result.pending_actions[0].id, actions, tool


async def test_write_tool_is_proposed_not_executed(session: AsyncSession) -> None:
    orchestrator, _, tool, _ = _setup(
        session, [DEMO_INTENT, [tool_call("demo_save_note", text="mua sữa")], "Bạn xác nhận nhé."]
    )

    result = await orchestrator.handle(
        user_id=DEFAULT_USER_ID, text="Ghi chú giúp mình", conversation_id=None
    )

    assert tool.saved == []
    assert [r.status for r in result.tool_results] == [ToolStatus.PENDING]
    assert len(result.pending_actions) == 1
    action = result.pending_actions[0]
    assert action.summary == "Lưu ghi chú: mua sữa"
    assert action.status is PendingActionStatus.PENDING
    stored = await session.get(PendingAction, action.id)
    assert stored is not None
    assert stored.arguments == {"text": "mua sữa"}


async def test_model_is_told_that_nothing_was_saved(session: AsyncSession) -> None:
    orchestrator, _, _, provider = _setup(
        session, [DEMO_INTENT, [tool_call("demo_save_note", text="x")], "ok"]
    )

    await orchestrator.handle(user_id=DEFAULT_USER_ID, text="Ghi chú", conversation_id=None)

    shown = provider.calls[2].messages[-1].content
    assert "awaiting_user_confirmation" in shown
    assert "Nothing has been saved" in shown


async def test_preview_error_is_reported_and_nothing_is_proposed(session: AsyncSession) -> None:
    orchestrator, _, tool, _ = _setup(
        session, [DEMO_INTENT, [tool_call("demo_save_note", text="forbidden")], "Không được."]
    )

    result = await orchestrator.handle(user_id=DEFAULT_USER_ID, text="Ghi", conversation_id=None)

    assert result.pending_actions == []
    assert result.tool_results[0].error_code == "note_forbidden"
    assert (await session.scalars(select(PendingAction))).all() == []
    assert tool.saved == []


async def test_confirm_runs_the_change_and_records_it(session: AsyncSession) -> None:
    action_id, actions, tool = await _propose(session)

    resolved = await actions.confirm(action_id, DEFAULT_USER_ID)

    assert resolved.status is PendingActionStatus.CONFIRMED
    assert resolved.result == {"saved": "mua sữa"}
    assert resolved.resolved_at is not None
    assert tool.saved == ["mua sữa"]
    note = (await session.scalars(select(Message).where(Message.role == MessageRole.SYSTEM))).one()
    assert "đã xác nhận" in note.content


async def test_cancel_changes_nothing(session: AsyncSession) -> None:
    action_id, actions, tool = await _propose(session)

    resolved = await actions.cancel(action_id, DEFAULT_USER_ID)

    assert resolved.status is PendingActionStatus.CANCELLED
    assert tool.saved == []


async def test_a_refused_change_is_recorded_as_failed(session: AsyncSession) -> None:
    action_id, actions, tool = await _propose(session, text="fails-later")

    resolved = await actions.confirm(action_id, DEFAULT_USER_ID)

    assert resolved.status is PendingActionStatus.FAILED
    assert resolved.error_code == "note_locked"
    assert resolved.error_message == "Ghi chú đã bị khóa."
    assert tool.saved == []


@pytest.mark.parametrize("second", ["confirm", "cancel"])
async def test_an_action_can_be_resolved_only_once(session: AsyncSession, second: str) -> None:
    action_id, actions, tool = await _propose(session)
    await actions.confirm(action_id, DEFAULT_USER_ID)

    with pytest.raises(PendingActionResolvedError):
        await getattr(actions, second)(action_id, DEFAULT_USER_ID)

    assert tool.saved == ["mua sữa"]


async def test_actions_of_another_user_are_not_found(session: AsyncSession) -> None:
    action_id, actions, tool = await _propose(session)
    other = User(display_name="Người khác")
    session.add(other)
    await session.commit()

    with pytest.raises(PendingActionNotFoundError):
        await actions.confirm(action_id, other.id)
    with pytest.raises(PendingActionNotFoundError):
        await actions.confirm(uuid.uuid4(), DEFAULT_USER_ID)

    assert tool.saved == []


async def test_confirm_validates_the_stored_arguments_again(session: AsyncSession) -> None:
    action_id, actions, tool = await _propose(session)
    stored = await session.get(PendingAction, action_id)
    assert stored is not None
    stored.arguments = {"text": ""}
    await session.commit()

    resolved = await actions.confirm(action_id, DEFAULT_USER_ID)

    assert resolved.status is PendingActionStatus.FAILED
    assert resolved.error_code == "invalid_tool_input"
    assert tool.saved == []
