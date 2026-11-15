from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_session
from app.modules.ai.actions import PendingActionRepository, PendingActionService
from app.modules.ai.orchestrator import Orchestrator
from app.modules.ai.providers.base import LLMProvider
from app.modules.ai.runtime import AIRuntime
from app.modules.memory.public import (
    ConversationService,
    MemoryService,
    get_conversation_service,
    get_memory_service,
)


def get_ai_runtime(request: Request) -> AIRuntime:
    runtime: AIRuntime = request.app.state.ai_runtime
    return runtime


def get_llm_provider(runtime: Annotated[AIRuntime, Depends(get_ai_runtime)]) -> LLMProvider:
    return runtime.provider


def get_pending_action_service(
    runtime: Annotated[AIRuntime, Depends(get_ai_runtime)],
    session: Annotated[AsyncSession, Depends(get_session)],
    conversations: Annotated[ConversationService, Depends(get_conversation_service)],
) -> PendingActionService:
    return PendingActionService(
        session=session,
        repository=PendingActionRepository(session),
        executor=runtime.executor,
        conversations=conversations,
    )


def get_orchestrator(
    runtime: Annotated[AIRuntime, Depends(get_ai_runtime)],
    conversations: Annotated[ConversationService, Depends(get_conversation_service)],
    memories: Annotated[MemoryService, Depends(get_memory_service)],
    actions: Annotated[PendingActionService, Depends(get_pending_action_service)],
) -> Orchestrator:
    return Orchestrator(
        provider=runtime.provider,
        intent_classifier=runtime.intent_classifier,
        registry=runtime.registry,
        executor=runtime.executor,
        conversations=conversations,
        memories=memories,
        actions=actions,
        limits=runtime.limits,
    )
