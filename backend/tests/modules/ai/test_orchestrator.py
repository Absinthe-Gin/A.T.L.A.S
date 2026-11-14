"""One chat turn, end to end, with a scripted model and a real database.

Assertions target behaviour (which tools ran, with what, what was stored),
never the exact wording a real model would produce.
"""

import json
import uuid
from collections.abc import Sequence
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ExternalServiceUnavailableError
from app.modules.ai.intent import INTENT_GENERAL, INTENT_UNKNOWN
from app.modules.ai.orchestrator import Orchestrator
from app.modules.ai.prompts import CLARIFICATION_REPLY, EMPTY_REPLY, TOOL_LIMIT_REPLY
from app.modules.ai.providers.base import LLMRole, ToolCall
from app.modules.ai.providers.mock import MockLLMProvider
from app.modules.memory.exceptions import ConversationNotFoundError
from app.modules.memory.models import (
    Conversation,
    Memory,
    MemoryCategory,
    MemorySource,
    Message,
    MessageRole,
)
from app.modules.memory.repository import (
    ConversationRepository,
    MemoryRepository,
    MessageRepository,
)
from app.modules.memory.service import ConversationService, MemoryService
from app.modules.users.models import DEFAULT_USER_ID, User
from app.shared.tools import Tool, ToolStatus
from tests.ai_support import BusinessFailureTool, EchoTool, build_runtime, tool_call

DEMO_INTENT = '{"intent": "demo"}'


def _orchestrator(
    session: AsyncSession,
    provider: MockLLMProvider,
    tools: Sequence[Tool[Any, Any]] = (),
    **limits: int,
) -> Orchestrator:
    runtime = build_runtime(provider, tools, **limits)
    return Orchestrator(
        provider=runtime.provider,
        intent_classifier=runtime.intent_classifier,
        registry=runtime.registry,
        executor=runtime.executor,
        conversations=ConversationService(
            session, ConversationRepository(session), MessageRepository(session)
        ),
        memories=MemoryService(MemoryRepository(session)),
        limits=runtime.limits,
    )


async def _stored(session: AsyncSession, conversation_id: uuid.UUID) -> list[Message]:
    statement = (
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.sequence)
    )
    return list((await session.scalars(statement)).all())


# --- Without tools ----------------------------------------------------------


async def test_plain_reply_starts_a_conversation_and_stores_both_messages(
    session: AsyncSession,
) -> None:
    provider = MockLLMProvider(["Chào bạn!"])

    result = await _orchestrator(session, provider).handle(
        user_id=DEFAULT_USER_ID, text="Xin chào", conversation_id=None
    )

    assert result.reply == "Chào bạn!"
    assert result.intent == INTENT_GENERAL
    assert result.tool_results == []
    # No tools are registered: one model call, no classification call.
    assert len(provider.calls) == 1
    assert provider.calls[0].tools is None

    conversation = await session.get(Conversation, result.conversation_id)
    assert conversation is not None
    assert conversation.title == "Xin chào"
    stored = await _stored(session, result.conversation_id)
    assert [(m.sequence, m.role, m.content) for m in stored] == [
        (0, MessageRole.USER, "Xin chào"),
        (1, MessageRole.ASSISTANT, "Chào bạn!"),
    ]
    assert stored[1].id == result.message_id
    assert stored[1].meta == {
        "intent": INTENT_GENERAL,
        "provider": "mock",
        "model": "mock-model",
        "iterations": 1,
        "status": "success",
    }


async def test_follow_up_message_sends_the_earlier_turns_to_the_model(
    session: AsyncSession,
) -> None:
    provider = MockLLMProvider(["Chào bạn!", "Bạn tên Minh."])
    orchestrator = _orchestrator(session, provider)
    first = await orchestrator.handle(
        user_id=DEFAULT_USER_ID, text="Tôi tên Minh", conversation_id=None
    )

    second = await orchestrator.handle(
        user_id=DEFAULT_USER_ID, text="Tôi tên gì?", conversation_id=first.conversation_id
    )

    assert second.conversation_id == first.conversation_id
    sent = [(m.role, m.content) for m in provider.calls[1].messages[1:]]
    assert sent == [
        (LLMRole.USER, "Tôi tên Minh"),
        (LLMRole.ASSISTANT, "Chào bạn!"),
        (LLMRole.USER, "Tôi tên gì?"),
    ]
    assert len(await _stored(session, first.conversation_id)) == 4


async def test_conversations_do_not_share_history(session: AsyncSession) -> None:
    provider = MockLLMProvider(["một", "hai"])
    orchestrator = _orchestrator(session, provider)
    await orchestrator.handle(user_id=DEFAULT_USER_ID, text="Bí mật A", conversation_id=None)

    await orchestrator.handle(user_id=DEFAULT_USER_ID, text="Chuyện B", conversation_id=None)

    sent = [m.content for m in provider.calls[1].messages[1:]]
    assert sent == ["Chuyện B"]


async def test_history_sent_to_the_model_is_limited(session: AsyncSession) -> None:
    provider = MockLLMProvider(["1", "2", "3"])
    orchestrator = _orchestrator(session, provider, context_max_messages=2)
    first = await orchestrator.handle(user_id=DEFAULT_USER_ID, text="a", conversation_id=None)
    await orchestrator.handle(
        user_id=DEFAULT_USER_ID, text="b", conversation_id=first.conversation_id
    )

    await orchestrator.handle(
        user_id=DEFAULT_USER_ID, text="c", conversation_id=first.conversation_id
    )

    sent = [m.content for m in provider.calls[2].messages[1:]]
    assert sent == ["b", "2", "c"]


async def test_relevant_memories_are_added_and_unrelated_ones_are_not(
    session: AsyncSession,
) -> None:
    session.add_all(
        [
            Memory(
                user_id=DEFAULT_USER_ID,
                category=MemoryCategory.PREFERENCE,
                content="Thích uống cà phê sữa đá",
                source=MemorySource.USER_CONFIRMED,
            ),
            Memory(
                user_id=DEFAULT_USER_ID,
                category=MemoryCategory.GOAL,
                content="Muốn chạy marathon",
                source=MemorySource.USER_CONFIRMED,
            ),
        ]
    )
    await session.commit()
    provider = MockLLMProvider(["Cà phê nhé"])

    await _orchestrator(session, provider).handle(
        user_id=DEFAULT_USER_ID, text="Sáng nay uống cà phê gì?", conversation_id=None
    )

    system_prompt = provider.calls[0].messages[0].content
    assert "Thích uống cà phê sữa đá" in system_prompt
    assert "marathon" not in system_prompt


# --- With tools -------------------------------------------------------------


async def test_tool_call_is_executed_and_its_result_is_returned_to_the_model(
    session: AsyncSession,
) -> None:
    echo = EchoTool()
    provider = MockLLMProvider(
        [DEMO_INTENT, [tool_call("demo_echo", text="chào", repeat=2)], "Kết quả: chào chào"]
    )

    result = await _orchestrator(session, provider, [echo]).handle(
        user_id=DEFAULT_USER_ID, text="Lặp lại chữ chào hai lần", conversation_id=None
    )

    assert result.reply == "Kết quả: chào chào"
    assert result.intent == "demo"
    assert [(r.tool_name, r.status) for r in result.tool_results] == [
        ("demo_echo", ToolStatus.SUCCESS)
    ]

    # The tool ran once, for the current user and conversation.
    context, tool_input = echo.received[0]
    assert context.user_id == DEFAULT_USER_ID
    assert context.conversation_id == result.conversation_id
    assert (tool_input.text, tool_input.repeat) == ("chào", 2)

    # The model was offered the tool, then shown its result.
    assert [tool.name for tool in provider.calls[1].tools or []] == ["demo_echo"]
    last_messages = provider.calls[2].messages[-2:]
    assert last_messages[0].tool_calls[0].name == "demo_echo"
    assert last_messages[1].role is LLMRole.TOOL
    assert json.loads(last_messages[1].content)["echoed"] == "chào chào"


async def test_tool_execution_is_recorded_in_the_conversation(session: AsyncSession) -> None:
    provider = MockLLMProvider(
        [DEMO_INTENT, [tool_call("demo_echo", call_id="call-7", text="a")], "a"]
    )

    result = await _orchestrator(session, provider, [EchoTool()]).handle(
        user_id=DEFAULT_USER_ID, text="Lặp lại a", conversation_id=None
    )

    stored = await _stored(session, result.conversation_id)
    assert [m.role for m in stored] == [
        MessageRole.USER,
        MessageRole.ASSISTANT,
        MessageRole.TOOL,
        MessageRole.ASSISTANT,
    ]
    request, execution, final = stored[1], stored[2], stored[3]
    assert request.meta == {
        "tool_calls": [{"id": "call-7", "name": "demo_echo", "arguments": {"text": "a"}}]
    }
    assert execution.tool_name == "demo_echo"
    assert execution.meta is not None
    assert execution.meta["tool_call_id"] == "call-7"
    assert execution.meta["status"] == "success"
    assert execution.meta["error_code"] is None
    assert final.meta is not None
    assert final.meta["iterations"] == 2


async def test_stored_tool_turns_are_replayed_in_the_next_turn(session: AsyncSession) -> None:
    provider = MockLLMProvider(
        [DEMO_INTENT, [tool_call("demo_echo", text="a")], "a", '{"intent": "general"}', "ok"]
    )
    orchestrator = _orchestrator(session, provider, [EchoTool()])
    first = await orchestrator.handle(
        user_id=DEFAULT_USER_ID, text="Lặp lại a", conversation_id=None
    )

    await orchestrator.handle(
        user_id=DEFAULT_USER_ID, text="Cảm ơn", conversation_id=first.conversation_id
    )

    replayed = provider.calls[-1].messages[1:]
    assert [m.role for m in replayed] == [
        LLMRole.USER,
        LLMRole.ASSISTANT,
        LLMRole.TOOL,
        LLMRole.ASSISTANT,
        LLMRole.USER,
    ]
    assert replayed[1].tool_calls[0].name == "demo_echo"


async def test_invalid_arguments_are_reported_to_the_model_so_it_can_retry(
    session: AsyncSession,
) -> None:
    echo = EchoTool()
    provider = MockLLMProvider(
        [
            DEMO_INTENT,
            [tool_call("demo_echo", text="a", repeat=99)],
            [tool_call("demo_echo", call_id="call-2", text="a", repeat=2)],
            "a a",
        ]
    )

    result = await _orchestrator(session, provider, [echo]).handle(
        user_id=DEFAULT_USER_ID, text="Lặp lại a", conversation_id=None
    )

    assert result.reply == "a a"
    assert [r.status for r in result.tool_results] == [ToolStatus.ERROR, ToolStatus.SUCCESS]
    assert result.tool_results[0].error_code == "invalid_tool_input"
    assert len(echo.received) == 1
    error_shown_to_model = json.loads(provider.calls[2].messages[-1].content)["error"]
    assert error_shown_to_model["code"] == "invalid_tool_input"
    assert "repeat" in error_shown_to_model["message"]


async def test_unknown_tool_requested_by_the_model_is_not_executed(session: AsyncSession) -> None:
    echo = EchoTool()
    provider = MockLLMProvider(
        [DEMO_INTENT, [tool_call("finance_delete_all")], "Mình không làm được việc đó."]
    )

    result = await _orchestrator(session, provider, [echo]).handle(
        user_id=DEFAULT_USER_ID, text="Xóa hết", conversation_id=None
    )

    assert result.tool_results[0].error_code == "tool_not_found"
    assert echo.received == []
    assert result.reply == "Mình không làm được việc đó."


async def test_tool_from_another_domain_is_not_offered_or_executed(session: AsyncSession) -> None:
    travel = EchoTool(name="travel_echo", domain="travel")
    provider = MockLLMProvider([DEMO_INTENT, [tool_call("travel_echo", text="a")], "xong"])

    result = await _orchestrator(session, provider, [EchoTool(), travel]).handle(
        user_id=DEFAULT_USER_ID, text="Lặp lại a", conversation_id=None
    )

    assert [tool.name for tool in provider.calls[1].tools or []] == ["demo_echo"]
    assert result.tool_results[0].error_code == "tool_not_found"
    assert travel.received == []


async def test_business_failure_of_a_tool_is_reported_to_the_model(session: AsyncSession) -> None:
    provider = MockLLMProvider(
        [DEMO_INTENT, [tool_call("demo_reject", text="a")], "Bạn đã vượt ngân sách."]
    )

    result = await _orchestrator(session, provider, [BusinessFailureTool()]).handle(
        user_id=DEFAULT_USER_ID, text="Ghi chi tiêu", conversation_id=None
    )

    assert result.reply == "Bạn đã vượt ngân sách."
    assert result.tool_results[0].error_code == "budget_exceeded"
    shown = json.loads(provider.calls[2].messages[-1].content)
    assert shown == {"error": {"code": "budget_exceeded", "message": "Vượt quá ngân sách."}}


async def test_several_tool_calls_in_one_response_are_all_executed(session: AsyncSession) -> None:
    echo = EchoTool()
    calls = [
        tool_call("demo_echo", call_id="c1", text="a"),
        tool_call("demo_echo", call_id="c2", text="b"),
    ]
    provider = MockLLMProvider([DEMO_INTENT, calls, "a và b"])

    result = await _orchestrator(session, provider, [echo]).handle(
        user_id=DEFAULT_USER_ID, text="Lặp lại a và b", conversation_id=None
    )

    assert [item[1].text for item in echo.received] == ["a", "b"]
    assert len(result.tool_results) == 2
    assert len(await _stored(session, result.conversation_id)) == 5


async def test_tool_loop_stops_at_the_iteration_limit(
    session: AsyncSession, caplog: pytest.LogCaptureFixture
) -> None:
    echo = EchoTool()
    endless: list[str | list[ToolCall] | Exception] = [DEMO_INTENT]
    endless += [[tool_call("demo_echo", call_id=f"c{i}", text="a")] for i in range(10)]
    provider = MockLLMProvider(endless)

    result = await _orchestrator(session, provider, [echo], max_tool_iterations=3).handle(
        user_id=DEFAULT_USER_ID, text="Lặp mãi", conversation_id=None
    )

    assert result.reply == TOOL_LIMIT_REPLY
    assert len(echo.received) == 3
    # One classification call plus exactly three generation calls.
    assert len(provider.calls) == 4
    stored = await _stored(session, result.conversation_id)
    assert stored[-1].meta is not None
    assert stored[-1].meta["status"] == "tool_limit_reached"
    assert any(record.message == "Tool iteration limit reached" for record in caplog.records)


# --- When the model misbehaves ----------------------------------------------


async def test_unknown_intent_asks_for_clarification_without_using_tools(
    session: AsyncSession,
) -> None:
    echo = EchoTool()
    provider = MockLLMProvider([f'{{"intent": "{INTENT_UNKNOWN}"}}'])

    result = await _orchestrator(session, provider, [echo]).handle(
        user_id=DEFAULT_USER_ID, text="asdf qwer", conversation_id=None
    )

    assert result.reply == CLARIFICATION_REPLY
    assert result.intent == INTENT_UNKNOWN
    assert len(provider.calls) == 1
    assert echo.received == []
    stored = await _stored(session, result.conversation_id)
    assert [m.role for m in stored] == [MessageRole.USER, MessageRole.ASSISTANT]


async def test_general_intent_does_not_offer_tools(session: AsyncSession) -> None:
    provider = MockLLMProvider(['{"intent": "general"}', "Chào bạn"])

    await _orchestrator(session, provider, [EchoTool()]).handle(
        user_id=DEFAULT_USER_ID, text="Chào", conversation_id=None
    )

    assert provider.calls[1].tools is None


@pytest.mark.parametrize("empty", ["", "   \n"])
async def test_empty_reply_is_replaced_by_a_fallback_message(
    session: AsyncSession, empty: str
) -> None:
    result = await _orchestrator(session, MockLLMProvider([empty])).handle(
        user_id=DEFAULT_USER_ID, text="Chào", conversation_id=None
    )

    assert result.reply == EMPTY_REPLY


async def test_provider_failure_propagates_but_keeps_the_user_message(
    session: AsyncSession,
) -> None:
    provider = MockLLMProvider([ExternalServiceUnavailableError(code="llm_unavailable")])

    with pytest.raises(ExternalServiceUnavailableError):
        await _orchestrator(session, provider).handle(
            user_id=DEFAULT_USER_ID, text="Đừng làm mất tin này", conversation_id=None
        )

    stored = (await session.scalars(select(Message))).all()
    assert [(m.role, m.content) for m in stored] == [(MessageRole.USER, "Đừng làm mất tin này")]


# --- Conversation ownership -------------------------------------------------


async def test_unknown_conversation_is_rejected_before_calling_the_model(
    session: AsyncSession,
) -> None:
    provider = MockLLMProvider()

    with pytest.raises(ConversationNotFoundError):
        await _orchestrator(session, provider).handle(
            user_id=DEFAULT_USER_ID, text="Chào", conversation_id=uuid.uuid4()
        )

    assert provider.calls == []


async def test_conversation_of_another_user_is_treated_as_missing(session: AsyncSession) -> None:
    other_user = User(display_name="Người khác")
    session.add(other_user)
    await session.flush()
    foreign = Conversation(user_id=other_user.id, title="Riêng tư")
    session.add(foreign)
    await session.commit()
    provider = MockLLMProvider()

    with pytest.raises(ConversationNotFoundError):
        await _orchestrator(session, provider).handle(
            user_id=DEFAULT_USER_ID, text="Chào", conversation_id=foreign.id
        )

    assert provider.calls == []
    assert await _stored(session, foreign.id) == []


async def test_turn_is_logged_with_the_fields_needed_for_debugging(
    session: AsyncSession, caplog: pytest.LogCaptureFixture
) -> None:
    provider = MockLLMProvider([DEMO_INTENT, [tool_call("demo_echo", text="a")], "a"])

    result = await _orchestrator(session, provider, [EchoTool()]).handle(
        user_id=DEFAULT_USER_ID, text="Lặp lại a", conversation_id=None
    )

    records = [r for r in caplog.records if r.message == "Chat turn completed"]
    assert len(records) == 1
    logged = records[0].__dict__
    assert logged["conversation_id"] == str(result.conversation_id)
    assert logged["message_id"] == str(result.message_id)
    assert logged["intent"] == "demo"
    assert logged["provider"] == "mock"
    assert logged["model"] == "mock-model"
    assert logged["tools"] == ["demo_echo"]
    assert logged["iterations"] == 2
    assert logged["status"] == "success"
    assert logged["duration_ms"] >= 0
