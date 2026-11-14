"""Adapter for the Ollama HTTP API (https://github.com/ollama/ollama/blob/main/docs/api.md)."""

import logging
import time
import uuid
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.exceptions import (
    ExternalServiceError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from app.modules.ai.exceptions import LLMInvalidResponseError, LLMNotConfiguredError
from app.modules.ai.providers.base import (
    LLMMessage,
    LLMResponse,
    LLMRole,
    ToolCall,
    ToolDefinition,
)

logger = logging.getLogger(__name__)

_AVAILABILITY_TIMEOUT_SECONDS = 2.0


class _OllamaFunctionCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class _OllamaToolCall(BaseModel):
    function: _OllamaFunctionCall


class _OllamaMessage(BaseModel):
    content: str = ""
    tool_calls: list[_OllamaToolCall] = Field(default_factory=list)


class _OllamaChatResponse(BaseModel):
    """The part of Ollama's response this adapter relies on."""

    model: str
    message: _OllamaMessage


def _to_wire_message(message: LLMMessage) -> dict[str, Any]:
    wire: dict[str, Any] = {"role": message.role.value, "content": message.content}
    if message.tool_calls:
        wire["tool_calls"] = [
            {"function": {"name": call.name, "arguments": call.arguments}}
            for call in message.tool_calls
        ]
    if message.role is LLMRole.TOOL and message.tool_name:
        wire["tool_name"] = message.tool_name
    return wire


def _to_wire_tool(tool: ToolDefinition) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        model: str,
        temperature: float,
        timeout_seconds: float,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self.model = model
        self._temperature = temperature
        self._timeout_seconds = timeout_seconds

    async def chat(
        self,
        messages: list[LLMMessage],
        *,
        tools: list[ToolDefinition] | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        if not self.model:
            raise LLMNotConfiguredError()

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [_to_wire_message(message) for message in messages],
            "stream": False,
            "options": {"temperature": self._temperature},
        }
        if tools:
            payload["tools"] = [_to_wire_tool(tool) for tool in tools]
        if response_schema is not None:
            payload["format"] = response_schema

        started_at = time.perf_counter()
        body = await self._post_chat(payload)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

        try:
            parsed = _OllamaChatResponse.model_validate(body)
        except ValidationError as error:
            logger.error(
                "Ollama returned an unexpected response shape",
                extra={"model": self.model, "error_count": error.error_count()},
            )
            raise LLMInvalidResponseError() from error

        return LLMResponse(
            content=parsed.message.content,
            # Ollama does not assign call IDs; generate them for traceability.
            tool_calls=[
                ToolCall(
                    id=uuid.uuid4().hex, name=call.function.name, arguments=call.function.arguments
                )
                for call in parsed.message.tool_calls
            ],
            provider=self.name,
            model=parsed.model,
            duration_ms=duration_ms,
        )

    async def _post_chat(self, payload: dict[str, Any]) -> object:
        """Send the request and translate every transport failure into an application error."""
        try:
            response = await self._client.post(
                f"{self._base_url}/api/chat", json=payload, timeout=self._timeout_seconds
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as error:
            logger.error(
                "Ollama request timed out",
                extra={"model": self.model, "timeout_seconds": self._timeout_seconds},
            )
            raise ExternalServiceTimeoutError(
                "Model AI phản hồi quá lâu. Vui lòng thử lại.", code="llm_timeout"
            ) from error
        except httpx.HTTPStatusError as error:
            logger.error(
                "Ollama returned an error status",
                extra={"model": self.model, "status_code": error.response.status_code},
            )
            raise ExternalServiceError(
                "Dịch vụ AI trả về lỗi.", code="llm_request_failed"
            ) from error
        except httpx.TransportError as error:
            logger.error(
                "Ollama is unreachable",
                extra={"base_url": self._base_url, "error_type": type(error).__name__},
            )
            raise ExternalServiceUnavailableError(
                "Không kết nối được tới dịch vụ AI (Ollama). Hãy kiểm tra Ollama đã chạy chưa.",
                code="llm_unavailable",
            ) from error
        except ValueError as error:
            # The body is not JSON.
            logger.error("Ollama returned a non-JSON body", extra={"model": self.model})
            raise LLMInvalidResponseError() from error

    async def is_available(self) -> bool:
        try:
            response = await self._client.get(
                f"{self._base_url}/api/version", timeout=_AVAILABILITY_TIMEOUT_SECONDS
            )
        except httpx.HTTPError:
            return False
        return response.is_success
