"""Build the message list sent to the model for one turn."""

from collections.abc import Sequence

from pydantic import ValidationError

from app.modules.ai.prompts import build_system_prompt
from app.modules.ai.providers.base import LLMMessage, LLMRole, ToolCall
from app.modules.memory.public import MemoryData, MessageData, MessageRole

# Key under which an assistant message stores the tool calls it requested.
META_TOOL_CALLS = "tool_calls"

_ROLES = {
    MessageRole.USER: LLMRole.USER,
    MessageRole.ASSISTANT: LLMRole.ASSISTANT,
    MessageRole.TOOL: LLMRole.TOOL,
    MessageRole.SYSTEM: LLMRole.SYSTEM,
}


def _stored_tool_calls(message: MessageData) -> list[ToolCall]:
    raw = (message.meta or {}).get(META_TOOL_CALLS, [])
    try:
        return [ToolCall.model_validate(item) for item in raw]
    except (ValidationError, TypeError):
        # Unreadable history must not break the conversation.
        return []


def _to_llm_message(message: MessageData) -> LLMMessage:
    return LLMMessage(
        role=_ROLES[message.role],
        content=message.content,
        tool_calls=_stored_tool_calls(message) if message.role is MessageRole.ASSISTANT else [],
        tool_name=message.tool_name,
    )


def _drop_orphaned_tool_results(history: Sequence[MessageData]) -> Sequence[MessageData]:
    """Remove tool results whose requesting assistant message was cut off by the window."""
    start = 0
    while start < len(history) and history[start].role is MessageRole.TOOL:
        start += 1
    return history[start:]


def build_context(
    *, history: Sequence[MessageData], memories: Sequence[MemoryData], user_text: str
) -> list[LLMMessage]:
    """System prompt (with relevant memories), earlier messages, then the new message."""
    return [
        LLMMessage(role=LLMRole.SYSTEM, content=build_system_prompt(memories)),
        *(_to_llm_message(message) for message in _drop_orphaned_tool_results(history)),
        LLMMessage(role=LLMRole.USER, content=user_text),
    ]
