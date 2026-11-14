"""Deterministic provider for tests and for running without an LLM."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.modules.ai.providers.base import LLMMessage, LLMResponse, ToolCall, ToolDefinition

DEFAULT_REPLY = "Đây là phản hồi giả lập. Hãy đặt LLM_PROVIDER=ollama để dùng model thật."


@dataclass(frozen=True)
class RecordedCall:
    messages: list[LLMMessage]
    tools: list[ToolDefinition] | None
    response_schema: dict[str, Any] | None


class MockLLMProvider:
    """Replays scripted responses in order and records every call it receives.

    A scripted item is a reply text, a list of tool calls, or an exception to
    raise. When the script is exhausted the provider returns `DEFAULT_REPLY`.
    """

    name = "mock"
    model = "mock-model"

    def __init__(self, script: Sequence[str | list[ToolCall] | Exception] = ()) -> None:
        self._script = list(script)
        self.calls: list[RecordedCall] = []

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        tools: list[ToolDefinition] | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        self.calls.append(RecordedCall(list(messages), tools, response_schema))

        step = self._script.pop(0) if self._script else DEFAULT_REPLY
        if isinstance(step, Exception):
            raise step
        if isinstance(step, str):
            return LLMResponse(content=step, provider=self.name, model=self.model)
        return LLMResponse(tool_calls=step, provider=self.name, model=self.model)

    async def is_available(self) -> bool:
        return True
