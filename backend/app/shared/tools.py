"""Tool contract shared by the AI core and the business modules.

A business module exposes a capability to the assistant by implementing
``Tool``. The AI core only knows this contract, never the module behind it.
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class ToolEffect(StrEnum):
    READ = "read"
    # The tool changes stored data.
    WRITE = "write"


@dataclass(frozen=True)
class ToolSpec:
    """Static description of a tool.

    ``input_model`` is the source of the JSON Schema sent to the model and of
    the validation applied to the arguments the model produces.
    """

    name: str
    description: str
    # Business area the tool belongs to; doubles as the intent that selects it.
    domain: str
    effect: ToolEffect
    input_model: type[BaseModel]
    output_model: type[BaseModel]


@dataclass(frozen=True)
class ToolContext:
    """Trusted facts about the current turn.

    Identity always comes from here. It is never an argument supplied by the model.
    """

    user_id: uuid.UUID
    conversation_id: uuid.UUID
    request_id: str | None = None


class Tool[InputT: BaseModel, OutputT: BaseModel](ABC):
    """One narrowly scoped operation the assistant may request.

    A tool translates validated input into a call to its own module's service.
    It must not contain business rules.
    """

    spec: ToolSpec

    @abstractmethod
    async def execute(self, context: ToolContext, tool_input: InputT) -> OutputT: ...

    async def preview(self, context: ToolContext, tool_input: InputT) -> str:
        """Describe, in the user's language, what `execute` would change.

        Required for `ToolEffect.WRITE` tools: their requests are shown to the
        user for confirmation instead of running. May raise `AppError` when the
        request can already be seen to fail (for example an unknown category).
        """
        raise NotImplementedError(f"Write tool {self.spec.name!r} must implement preview().")


class ToolStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    # A write request that waits for the user to confirm it. Nothing has changed yet.
    PENDING = "pending"


class ToolResult(BaseModel):
    """Outcome of one tool execution. Failures are data, not exceptions."""

    tool_name: str
    status: ToolStatus
    output: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    duration_ms: float = 0.0

    @property
    def succeeded(self) -> bool:
        return self.status is ToolStatus.SUCCESS
