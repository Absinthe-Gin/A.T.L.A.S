"""Provider-neutral LLM interface.

The AI core talks only to ``LLMProvider``. Each adapter converts these types
to and from the wire format of one vendor.
"""

from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, Field


class LLMRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    """A request from the model to run one tool. Arguments are untrusted."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LLMMessage(BaseModel):
    role: LLMRole
    content: str = ""
    # Set on assistant messages that request tools.
    tool_calls: list[ToolCall] = Field(default_factory=list)
    # Set on tool messages: which tool produced `content`.
    tool_name: str | None = None


class ToolDefinition(BaseModel):
    """What the model is told about a tool."""

    name: str
    description: str
    # JSON Schema of the arguments.
    parameters: dict[str, Any]


class LLMResponse(BaseModel):
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    provider: str
    model: str
    duration_ms: float = 0.0


class LLMProvider(Protocol):
    """Adapter contract for a chat-capable language model."""

    name: str
    model: str

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        tools: list[ToolDefinition] | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Generate the next assistant message.

        `response_schema` asks for a JSON document matching the schema. The
        caller must still validate the result.

        Raises `ExternalServiceError` (or a subclass) when the provider fails.
        """
        ...

    async def is_available(self) -> bool:
        """Report whether the provider can be reached. Never raises."""
        ...
