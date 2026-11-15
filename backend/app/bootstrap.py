"""Composition root: the only place that knows every module.

Long-lived components are assembled here, and business modules register the
tools they offer to the assistant. The AI core itself never imports them.
"""

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.infrastructure.external import ExternalServices
from app.modules.ai.public import (
    AIRuntime,
    LLMIntentClassifier,
    OrchestratorLimits,
    ToolExecutor,
    ToolRegistry,
    build_llm_provider,
)
from app.modules.finance.public import build_finance_tools
from app.modules.food.public import build_food_tools
from app.modules.travel.public import build_travel_tools


def build_tool_registry(
    session_factory: async_sessionmaker[AsyncSession], external: ExternalServices
) -> ToolRegistry:
    """Collect the tools of every business module.

    Tools run outside the HTTP request, so each opens its own session from
    `session_factory`.
    """
    registry = ToolRegistry()
    for tool in build_finance_tools(session_factory):
        registry.register(tool)
    for tool in build_travel_tools(session_factory, external):
        registry.register(tool)
    for tool in build_food_tools(external):
        registry.register(tool)
    return registry


def build_ai_runtime(
    settings: Settings,
    http_client: httpx.AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
    external: ExternalServices,
) -> AIRuntime:
    """Assemble the AI components. Does not contact the LLM provider."""
    provider = build_llm_provider(settings, http_client)
    registry = build_tool_registry(session_factory, external)
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
