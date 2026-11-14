"""Single-agent orchestration of one chat turn.

The model proposes; this code validates and executes. The model never touches
the database and never runs business logic.
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, field

from app.core.request_context import get_request_id
from app.modules.ai.context import META_TOOL_CALLS, build_context
from app.modules.ai.execution_log import log_turn
from app.modules.ai.intent import INTENT_GENERAL, INTENT_UNKNOWN, IntentClassifier
from app.modules.ai.prompts import CLARIFICATION_REPLY, EMPTY_REPLY, TOOL_LIMIT_REPLY
from app.modules.ai.providers.base import LLMMessage, LLMProvider, LLMRole
from app.modules.ai.tools.executor import ToolExecutor
from app.modules.ai.tools.registry import ToolRegistry, to_definition
from app.modules.memory.public import ConversationService, MemoryService, MessageRole
from app.shared.tools import ToolContext, ToolResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrchestratorLimits:
    max_tool_iterations: int
    context_max_messages: int
    memory_limit: int


@dataclass(frozen=True)
class ChatTurnResult:
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    reply: str
    intent: str
    tool_results: list[ToolResult] = field(default_factory=list)


def _tool_message_content(result: ToolResult) -> str:
    """What the model is told about a tool execution. Carries no internal details."""
    if result.succeeded:
        return json.dumps(result.output, ensure_ascii=False)
    return json.dumps(
        {"error": {"code": result.error_code, "message": result.error_message}},
        ensure_ascii=False,
    )


class Orchestrator:
    def __init__(
        self,
        *,
        provider: LLMProvider,
        intent_classifier: IntentClassifier,
        registry: ToolRegistry,
        executor: ToolExecutor,
        conversations: ConversationService,
        memories: MemoryService,
        limits: OrchestratorLimits,
    ) -> None:
        self._provider = provider
        self._intent_classifier = intent_classifier
        self._registry = registry
        self._executor = executor
        self._conversations = conversations
        self._memories = memories
        self._limits = limits

    async def handle(
        self, *, user_id: uuid.UUID, text: str, conversation_id: uuid.UUID | None
    ) -> ChatTurnResult:
        """Process one user message and return the assistant's reply.

        The user message is stored before the model is called, so a provider
        failure never loses it. Provider failures propagate to the caller.
        """
        started_at = time.perf_counter()

        if conversation_id is None:
            conversation = await self._conversations.start_conversation(user_id, text)
        else:
            conversation = await self._conversations.get_conversation(conversation_id, user_id)

        history = await self._conversations.list_recent_messages(
            conversation.id, self._limits.context_max_messages
        )
        await self._conversations.append_message(conversation.id, MessageRole.USER, text)
        memories = await self._memories.find_relevant(user_id, text, self._limits.memory_limit)

        intent = await self._intent_classifier.classify(text, self._registry.domains())

        tool_results: list[ToolResult] = []
        iterations = 0
        status = "success"
        if intent == INTENT_UNKNOWN:
            reply, status = CLARIFICATION_REPLY, "clarification"
        else:
            messages = build_context(history=history, memories=memories, user_text=text)
            context = ToolContext(
                user_id=user_id, conversation_id=conversation.id, request_id=get_request_id()
            )
            reply, iterations, limit_reached = await self._run_tool_loop(
                messages, intent, context, tool_results
            )
            if limit_reached:
                reply, status = TOOL_LIMIT_REPLY, "tool_limit_reached"
                logger.warning(
                    "Tool iteration limit reached",
                    extra={"conversation_id": str(conversation.id), "limit": iterations},
                )
            elif not reply.strip():
                reply, status = EMPTY_REPLY, "empty_reply"
                logger.warning(
                    "Model returned an empty reply",
                    extra={"conversation_id": str(conversation.id)},
                )

        assistant_message = await self._conversations.append_message(
            conversation.id,
            MessageRole.ASSISTANT,
            reply,
            meta={
                "intent": intent,
                "provider": self._provider.name,
                "model": self._provider.model,
                "iterations": iterations,
                "status": status,
            },
        )
        log_turn(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            intent=intent,
            provider=self._provider.name,
            model=self._provider.model,
            iterations=iterations,
            tool_names=[result.tool_name for result in tool_results],
            duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            status=status,
        )
        return ChatTurnResult(
            conversation_id=conversation.id,
            message_id=assistant_message.id,
            reply=reply,
            intent=intent,
            tool_results=tool_results,
        )

    async def _run_tool_loop(
        self,
        messages: list[LLMMessage],
        intent: str,
        context: ToolContext,
        tool_results: list[ToolResult],
    ) -> tuple[str, int, bool]:
        """Call the model until it answers in text.

        Returns the reply, the number of model calls, and whether the
        iteration limit stopped the loop before a text answer was produced.
        """
        tools = [] if intent == INTENT_GENERAL else self._registry.for_domain(intent)
        definitions = [to_definition(tool) for tool in tools] or None
        allowed_tools = {tool.spec.name for tool in tools}

        for iteration in range(1, self._limits.max_tool_iterations + 1):
            response = await self._provider.chat(messages, tools=definitions)
            if not response.tool_calls:
                return response.content, iteration, False

            messages.append(
                LLMMessage(
                    role=LLMRole.ASSISTANT,
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )
            await self._conversations.append_message(
                context.conversation_id,
                MessageRole.ASSISTANT,
                response.content,
                meta={
                    META_TOOL_CALLS: [call.model_dump(mode="json") for call in response.tool_calls]
                },
            )

            for call in response.tool_calls:
                result = await self._executor.execute(call, context, allowed_tools)
                tool_results.append(result)
                content = _tool_message_content(result)
                messages.append(LLMMessage(role=LLMRole.TOOL, content=content, tool_name=call.name))
                await self._conversations.append_message(
                    context.conversation_id,
                    MessageRole.TOOL,
                    content,
                    tool_name=call.name,
                    meta={
                        "tool_call_id": call.id,
                        "status": result.status.value,
                        "error_code": result.error_code,
                        "duration_ms": result.duration_ms,
                    },
                )

        return "", self._limits.max_tool_iterations, True
