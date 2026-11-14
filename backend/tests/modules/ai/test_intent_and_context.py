import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from app.core.exceptions import ExternalServiceUnavailableError
from app.modules.ai.context import build_context
from app.modules.ai.intent import INTENT_GENERAL, INTENT_UNKNOWN, LLMIntentClassifier
from app.modules.ai.prompts import SYSTEM_PROMPT
from app.modules.ai.providers.base import LLMRole
from app.modules.ai.providers.mock import MockLLMProvider
from app.modules.memory.models import MemoryCategory
from app.modules.memory.public import MemoryData, MemorySource, MessageData, MessageRole

DOMAINS = ["finance", "travel"]
CONVERSATION_ID = uuid.uuid4()


# --- Intent classification --------------------------------------------------


@pytest.mark.parametrize("intent", ["finance", "travel", INTENT_GENERAL, INTENT_UNKNOWN])
async def test_classifier_returns_a_valid_intent_from_the_model(intent: str) -> None:
    provider = MockLLMProvider([f'{{"intent": "{intent}"}}'])

    assert await LLMIntentClassifier(provider).classify("Tháng này tôi tiêu gì?", DOMAINS) == intent


async def test_classifier_restricts_the_model_to_the_known_intents() -> None:
    provider = MockLLMProvider(['{"intent": "finance"}'])

    await LLMIntentClassifier(provider).classify("Ghi chi tiêu 50k", DOMAINS)

    call = provider.calls[0]
    assert call.response_schema is not None
    assert call.response_schema["properties"]["intent"]["enum"] == [
        "finance",
        "travel",
        INTENT_GENERAL,
        INTENT_UNKNOWN,
    ]
    assert call.tools is None
    assert call.messages[-1].content == "Ghi chi tiêu 50k"


async def test_classifier_skips_the_model_when_no_tools_exist() -> None:
    provider = MockLLMProvider()

    intent = await LLMIntentClassifier(provider).classify("Xin chào", [])

    assert intent == INTENT_GENERAL
    assert provider.calls == []


@pytest.mark.parametrize(
    "content",
    [
        "không phải JSON",
        "",
        '{"intent": "weather"}',
        '{"something_else": "finance"}',
        '{"intent": 5}',
        '["finance"]',
    ],
)
async def test_classifier_falls_back_to_general_on_an_invalid_answer(
    content: str, caplog: pytest.LogCaptureFixture
) -> None:
    provider = MockLLMProvider([content])

    intent = await LLMIntentClassifier(provider).classify("…", DOMAINS)

    assert intent == INTENT_GENERAL
    assert any("invalid result" in record.message for record in caplog.records)


async def test_classifier_lets_provider_failures_propagate() -> None:
    provider = MockLLMProvider([ExternalServiceUnavailableError()])

    with pytest.raises(ExternalServiceUnavailableError):
        await LLMIntentClassifier(provider).classify("…", DOMAINS)


# --- Conversation context ---------------------------------------------------


def _message(
    sequence: int,
    role: MessageRole,
    content: str,
    *,
    tool_name: str | None = None,
    meta: dict[str, Any] | None = None,
) -> MessageData:
    return MessageData(
        id=uuid.uuid4(),
        conversation_id=CONVERSATION_ID,
        sequence=sequence,
        role=role,
        content=content,
        tool_name=tool_name,
        meta=meta,
        created_at=datetime.now(UTC),
    )


def _memory(content: str, source: MemorySource) -> MemoryData:
    return MemoryData(
        id=uuid.uuid4(),
        category=MemoryCategory.PREFERENCE,
        content=content,
        source=source,
        created_at=datetime.now(UTC),
    )


def test_context_is_system_prompt_then_history_then_the_new_message() -> None:
    history = [
        _message(0, MessageRole.USER, "Chào"),
        _message(1, MessageRole.ASSISTANT, "Chào bạn"),
    ]

    messages = build_context(history=history, memories=[], user_text="Hôm nay thế nào?")

    assert [(m.role, m.content) for m in messages] == [
        (LLMRole.SYSTEM, SYSTEM_PROMPT),
        (LLMRole.USER, "Chào"),
        (LLMRole.ASSISTANT, "Chào bạn"),
        (LLMRole.USER, "Hôm nay thế nào?"),
    ]


def test_context_without_history_has_only_the_prompt_and_the_message() -> None:
    messages = build_context(history=[], memories=[], user_text="Chào")

    assert [m.role for m in messages] == [LLMRole.SYSTEM, LLMRole.USER]


def test_context_adds_memories_with_their_origin_to_the_system_prompt() -> None:
    memories = [
        _memory("Thích ăn phở", MemorySource.USER_CONFIRMED),
        _memory("Có thể đang ăn kiêng", MemorySource.AI_INFERRED),
    ]

    system = build_context(history=[], memories=memories, user_text="Ăn gì?")[0].content

    assert system.startswith(SYSTEM_PROMPT)
    assert "- Thích ăn phở (người dùng xác nhận)" in system
    assert "- Có thể đang ăn kiêng (AI suy luận, chưa xác nhận)" in system


def test_context_restores_tool_calls_and_tool_results_from_history() -> None:
    stored_call = {"id": "c1", "name": "demo_echo", "arguments": {"text": "a"}}
    history = [
        _message(0, MessageRole.USER, "Lặp lại a"),
        _message(1, MessageRole.ASSISTANT, "", meta={"tool_calls": [stored_call]}),
        _message(2, MessageRole.TOOL, '{"echoed": "a"}', tool_name="demo_echo"),
        _message(3, MessageRole.ASSISTANT, "a", meta={"intent": "demo"}),
    ]

    messages = build_context(history=history, memories=[], user_text="Tiếp")

    assistant_call, tool_result, final = messages[2], messages[3], messages[4]
    assert assistant_call.tool_calls[0].name == "demo_echo"
    assert assistant_call.tool_calls[0].arguments == {"text": "a"}
    assert tool_result.role is LLMRole.TOOL
    assert tool_result.tool_name == "demo_echo"
    assert final.tool_calls == []


def test_context_drops_tool_results_cut_off_from_their_request() -> None:
    history = [
        _message(5, MessageRole.TOOL, '{"echoed": "a"}', tool_name="demo_echo"),
        _message(6, MessageRole.TOOL, '{"echoed": "b"}', tool_name="demo_echo"),
        _message(7, MessageRole.ASSISTANT, "a b"),
    ]

    messages = build_context(history=history, memories=[], user_text="Tiếp")

    assert [m.role for m in messages] == [LLMRole.SYSTEM, LLMRole.ASSISTANT, LLMRole.USER]


@pytest.mark.parametrize("stored", ["not-a-list", [{"name": "missing id"}], [5], None])
def test_context_ignores_unreadable_stored_tool_calls(stored: object) -> None:
    history = [_message(0, MessageRole.ASSISTANT, "trả lời", meta={"tool_calls": stored})]

    messages = build_context(history=history, memories=[], user_text="Tiếp")

    assert messages[1].content == "trả lời"
    assert messages[1].tool_calls == []
