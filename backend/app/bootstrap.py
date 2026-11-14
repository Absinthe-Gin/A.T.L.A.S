"""Composition root: the only place that knows every module.

Long-lived components are assembled here, and business modules register the
tools they offer to the assistant. The AI core itself never imports them.
"""

import httpx

from app.core.config import Settings
from app.modules.ai.public import (
    AIRuntime,
    LLMIntentClassifier,
    OrchestratorLimits,
    ToolExecutor,
    ToolRegistry,
    build_llm_provider,
)


def build_tool_registry() -> ToolRegistry:
    """Collect the tools of every business module.

    No business module exists yet, so the registry starts empty. A module adds
    its tools here, for example: ``registry.register(CreateTransactionTool(...))``.
    """
    return ToolRegistry()


def build_ai_runtime(settings: Settings, http_client: httpx.AsyncClient) -> AIRuntime:
    """Assemble the AI components. Does not contact the LLM provider."""
    provider = build_llm_provider(settings, http_client)
    registry = build_tool_registry()
    return AIRuntime(
        provider=provider,
        intent_classifier=LLMIntentClassifier(provider),
        registry=registry,
        executor=ToolExecutor(registry, settings.ai_tool_timeout_seconds),
        limits=OrchestratorLimits(
            max_tool_iterations=settings.ai_max_tool_iterations,
            context_max_messages=settings.ai_context_max_messages,
            memory_limit=settings.ai_memory_limit,
        ),
    )
