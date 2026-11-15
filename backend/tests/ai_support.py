"""Sample tools and builders used by the AI tests."""

import asyncio
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError
from app.modules.ai.actions import PendingActionRepository, PendingActionService
from app.modules.ai.intent import LLMIntentClassifier
from app.modules.ai.orchestrator import OrchestratorLimits
from app.modules.ai.providers.base import LLMProvider, ToolCall
from app.modules.ai.runtime import AIRuntime
from app.modules.ai.tools.executor import ToolExecutor
from app.modules.ai.tools.registry import ToolRegistry
from app.modules.memory.repository import ConversationRepository, MessageRepository
from app.modules.memory.service import ConversationService
from app.shared.tools import Tool, ToolContext, ToolEffect, ToolSpec


class EchoInput(BaseModel):
    text: str = Field(min_length=1, max_length=50)
    repeat: int = Field(default=1, ge=1, le=3)


class EchoOutput(BaseModel):
    echoed: str
    user_id: str


def _spec(name: str, *, domain: str = "demo", effect: ToolEffect = ToolEffect.READ) -> ToolSpec:
    return ToolSpec(
        name=name,
        description="Repeat the given text.",
        domain=domain,
        effect=effect,
        input_model=EchoInput,
        output_model=EchoOutput,
    )


class EchoTool(Tool[EchoInput, EchoOutput]):
    """Succeeds and records the inputs it was called with."""

    def __init__(self, name: str = "demo_echo", domain: str = "demo") -> None:
        self.spec = _spec(name, domain=domain)
        self.received: list[tuple[ToolContext, EchoInput]] = []

    async def execute(self, context: ToolContext, tool_input: EchoInput) -> EchoOutput:
        self.received.append((context, tool_input))
        return EchoOutput(
            echoed=" ".join([tool_input.text] * tool_input.repeat), user_id=str(context.user_id)
        )


class BusinessFailureTool(Tool[EchoInput, EchoOutput]):
    spec = _spec("demo_reject")

    async def execute(self, context: ToolContext, tool_input: EchoInput) -> EchoOutput:
        raise BusinessRuleError("Vượt quá ngân sách.", code="budget_exceeded")


class CrashingTool(Tool[EchoInput, EchoOutput]):
    spec = _spec("demo_crash")

    async def execute(self, context: ToolContext, tool_input: EchoInput) -> EchoOutput:
        raise RuntimeError("secret internal detail")


class SlowTool(Tool[EchoInput, EchoOutput]):
    spec = _spec("demo_slow")

    async def execute(self, context: ToolContext, tool_input: EchoInput) -> EchoOutput:
        await asyncio.sleep(5)
        return EchoOutput(echoed="late", user_id="")


class BadOutputTool(Tool[EchoInput, EchoOutput]):
    spec = _spec("demo_bad_output")

    async def execute(self, context: ToolContext, tool_input: EchoInput) -> EchoOutput:
        return {"unexpected": True}  # type: ignore[return-value]


def tool_call(name: str, call_id: str = "call-1", **arguments: Any) -> ToolCall:
    return ToolCall(id=call_id, name=name, arguments=arguments)


def build_registry(tools: Sequence[Tool[Any, Any]] = ()) -> ToolRegistry:
    registry = ToolRegistry()
    for tool in tools:
        registry.register(tool)
    return registry


def build_runtime(
    provider: LLMProvider,
    tools: Sequence[Tool[Any, Any]] = (),
    *,
    max_tool_iterations: int = 3,
    context_max_messages: int = 20,
    memory_limit: int = 5,
    tool_timeout_seconds: float = 0.2,
) -> AIRuntime:
    registry = build_registry(tools)
    return AIRuntime(
        provider=provider,
        intent_classifier=LLMIntentClassifier(provider),
        registry=registry,
        executor=ToolExecutor(registry, tool_timeout_seconds),
        limits=OrchestratorLimits(
            max_tool_iterations=max_tool_iterations,
            context_max_messages=context_max_messages,
            memory_limit=memory_limit,
        ),
    )


class NoteInput(BaseModel):
    text: str = Field(min_length=1, max_length=50)


class SavedNote(BaseModel):
    saved: str


class SaveNoteTool(Tool[NoteInput, SavedNote]):
    """A write tool: the model can only propose it; it runs after confirmation."""

    def __init__(self) -> None:
        self.spec = ToolSpec(
            name="demo_save_note",
            description="Save a note.",
            domain="demo",
            effect=ToolEffect.WRITE,
            input_model=NoteInput,
            output_model=SavedNote,
        )
        self.saved: list[str] = []

    async def preview(self, context: ToolContext, tool_input: NoteInput) -> str:
        if tool_input.text == "forbidden":
            raise BusinessRuleError("Không được lưu ghi chú này.", code="note_forbidden")
        return f"Lưu ghi chú: {tool_input.text}"

    async def execute(self, context: ToolContext, tool_input: NoteInput) -> SavedNote:
        if tool_input.text == "fails-later":
            raise BusinessRuleError("Ghi chú đã bị khóa.", code="note_locked")
        self.saved.append(tool_input.text)
        return SavedNote(saved=tool_input.text)


def build_actions(session: AsyncSession, runtime: AIRuntime) -> PendingActionService:
    return PendingActionService(
        session=session,
        repository=PendingActionRepository(session),
        executor=runtime.executor,
        conversations=ConversationService(
            session, ConversationRepository(session), MessageRepository(session)
        ),
    )
