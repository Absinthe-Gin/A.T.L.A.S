from typing import Annotated

from fastapi import Depends, Request

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


def get_orchestrator(
    runtime: Annotated[AIRuntime, Depends(get_ai_runtime)],
    conversations: Annotated[ConversationService, Depends(get_conversation_service)],
    memories: Annotated[MemoryService, Depends(get_memory_service)],
) -> Orchestrator:
    return Orchestrator(
        provider=runtime.provider,
        intent_classifier=runtime.intent_classifier,
        registry=runtime.registry,
        executor=runtime.executor,
        conversations=conversations,
        memories=memories,
        limits=runtime.limits,
    )
