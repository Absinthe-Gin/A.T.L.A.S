import httpx

from app.core.config import LLMProviderName, Settings
from app.modules.ai.providers.base import LLMProvider
from app.modules.ai.providers.mock import MockLLMProvider
from app.modules.ai.providers.ollama import OllamaProvider


def build_llm_provider(settings: Settings, http_client: httpx.AsyncClient) -> LLMProvider:
    """Create the configured provider. Never contacts the provider."""
    if settings.llm_provider is LLMProviderName.MOCK:
        return MockLLMProvider()
    return OllamaProvider(
        http_client,
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=settings.llm_temperature,
        timeout_seconds=settings.llm_timeout_seconds,
    )
