import logging
from collections.abc import Sequence
from typing import Protocol

from pydantic import BaseModel, ValidationError

from app.modules.ai.prompts import INTENT_PROMPT
from app.modules.ai.providers.base import LLMMessage, LLMProvider, LLMRole

logger = logging.getLogger(__name__)

# Answer directly, without tools.
INTENT_GENERAL = "general"
# The request could not be understood: ask the user to clarify.
INTENT_UNKNOWN = "unknown"


class IntentClassifier(Protocol):
    async def classify(self, text: str, domains: Sequence[str]) -> str:
        """Return one of `domains`, `INTENT_GENERAL` or `INTENT_UNKNOWN`."""
        ...


class _IntentOutput(BaseModel):
    intent: str


class LLMIntentClassifier:
    """Ask the model which tool domain, if any, a message belongs to."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def classify(self, text: str, domains: Sequence[str]) -> str:
        if not domains:
            # No tools are registered, so there is nothing to choose between.
            return INTENT_GENERAL

        allowed = [*domains, INTENT_GENERAL, INTENT_UNKNOWN]
        response = await self._provider.chat(
            [
                LLMMessage(
                    role=LLMRole.SYSTEM, content=INTENT_PROMPT.format(intents=", ".join(allowed))
                ),
                LLMMessage(role=LLMRole.USER, content=text),
            ],
            response_schema={
                "type": "object",
                "properties": {"intent": {"type": "string", "enum": allowed}},
                "required": ["intent"],
            },
        )

        try:
            intent = _IntentOutput.model_validate_json(response.content).intent
        except ValidationError:
            intent = ""
        if intent not in allowed:
            # Answering without tools cannot change data, so it is the safe fallback.
            logger.warning(
                "Intent classification returned an invalid result; using 'general'",
                extra={"model": response.model},
            )
            return INTENT_GENERAL
        return intent
