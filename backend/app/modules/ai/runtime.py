from dataclasses import dataclass

from app.modules.ai.intent import IntentClassifier
from app.modules.ai.orchestrator import OrchestratorLimits
from app.modules.ai.providers.base import LLMProvider
from app.modules.ai.tools.executor import ToolExecutor
from app.modules.ai.tools.registry import ToolRegistry


@dataclass(frozen=True)
class AIRuntime:
    """Long-lived AI components, created once at startup by the composition root."""

    provider: LLMProvider
    intent_classifier: IntentClassifier
    registry: ToolRegistry
    executor: ToolExecutor
    limits: OrchestratorLimits
