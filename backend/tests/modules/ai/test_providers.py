"""LLM provider adapters. No test contacts a real Ollama server."""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from app.core.config import LLMProviderName, Settings
from app.core.exceptions import (
    ExternalServiceError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from app.modules.ai.exceptions import LLMInvalidResponseError, LLMNotConfiguredError
from app.modules.ai.providers.base import LLMMessage, LLMRole, ToolCall, ToolDefinition
from app.modules.ai.providers.factory import build_llm_provider
from app.modules.ai.providers.mock import DEFAULT_REPLY, MockLLMProvider
from app.modules.ai.providers.ollama import OllamaProvider

Handler = Callable[[httpx.Request], httpx.Response]

USER_MESSAGE = [LLMMessage(role=LLMRole.USER, content="Xin chào")]


def _ollama(handler: Handler, model: str = "test-model") -> OllamaProvider:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OllamaProvider(
        client,
        base_url="http://ollama.test:11434/",
        model=model,
        temperature=0.3,
        timeout_seconds=5,
    )


def _reply(message: dict[str, Any], model: str = "test-model") -> httpx.Response:
    return httpx.Response(200, json={"model": model, "message": message, "done": True})


# --- Ollama: request --------------------------------------------------------


async def test_ollama_sends_model_messages_and_options() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return _reply({"role": "assistant", "content": "Chào bạn"})

    await _ollama(handler).chat(
        [LLMMessage(role=LLMRole.SYSTEM, content="Bạn là trợ lý."), *USER_MESSAGE]
    )

    assert captured["url"] == "http://ollama.test:11434/api/chat"
    assert captured["body"] == {
        "model": "test-model",
        "messages": [
            {"role": "system", "content": "Bạn là trợ lý."},
            {"role": "user", "content": "Xin chào"},
        ],
        "stream": False,
        "options": {"temperature": 0.3},
    }


async def test_ollama_sends_tools_and_response_schema_when_given() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return _reply({"role": "assistant", "content": "{}"})

    schema = {"type": "object", "properties": {"intent": {"type": "string"}}}
    parameters = {"type": "object", "properties": {"city": {"type": "string"}}}
    await _ollama(handler).chat(
        USER_MESSAGE,
        tools=[ToolDefinition(name="travel_search", description="Tìm", parameters=parameters)],
        response_schema=schema,
    )

    assert captured["format"] == schema
    assert captured["tools"] == [
        {
            "type": "function",
            "function": {"name": "travel_search", "description": "Tìm", "parameters": parameters},
        }
    ]


async def test_ollama_sends_earlier_tool_calls_and_tool_results() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return _reply({"role": "assistant", "content": "Xong"})

    await _ollama(handler).chat(
        [
            *USER_MESSAGE,
            LLMMessage(
                role=LLMRole.ASSISTANT,
                tool_calls=[ToolCall(id="c1", name="demo_echo", arguments={"text": "a"})],
            ),
            LLMMessage(role=LLMRole.TOOL, content='{"echoed": "a"}', tool_name="demo_echo"),
        ]
    )

    assert captured["messages"][1] == {
        "role": "assistant",
        "content": "",
        "tool_calls": [{"function": {"name": "demo_echo", "arguments": {"text": "a"}}}],
    }
    assert captured["messages"][2] == {
        "role": "tool",
        "content": '{"echoed": "a"}',
        "tool_name": "demo_echo",
    }


# --- Ollama: response -------------------------------------------------------


async def test_ollama_returns_the_text_reply() -> None:
    provider = _ollama(lambda _: _reply({"role": "assistant", "content": "Chào bạn"}, "served"))

    response = await provider.chat(USER_MESSAGE)

    assert response.content == "Chào bạn"
    assert response.tool_calls == []
    assert response.provider == "ollama"
    assert response.model == "served"
    assert response.duration_ms >= 0


async def test_ollama_returns_tool_calls_with_generated_ids() -> None:
    message = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {"function": {"name": "demo_echo", "arguments": {"text": "a"}}},
            {"function": {"name": "demo_echo", "arguments": {"text": "b"}}},
        ],
    }

    response = await _ollama(lambda _: _reply(message)).chat(USER_MESSAGE)

    assert [(call.name, call.arguments) for call in response.tool_calls] == [
        ("demo_echo", {"text": "a"}),
        ("demo_echo", {"text": "b"}),
    ]
    ids = [call.id for call in response.tool_calls]
    assert all(ids) and len(set(ids)) == 2


# --- Ollama: failures -------------------------------------------------------


async def test_ollama_without_a_model_fails_before_any_request() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise AssertionError("no request expected")

    with pytest.raises(LLMNotConfiguredError) as error:
        await _ollama(handler, model="").chat(USER_MESSAGE)

    assert error.value.status_code == 503
    assert error.value.code == "llm_not_configured"


async def test_ollama_connection_failure_is_reported_as_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(ExternalServiceUnavailableError) as error:
        await _ollama(handler).chat(USER_MESSAGE)

    assert error.value.code == "llm_unavailable"
    assert isinstance(error.value.__cause__, httpx.ConnectError)


async def test_ollama_timeout_is_reported_as_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with pytest.raises(ExternalServiceTimeoutError) as error:
        await _ollama(handler).chat(USER_MESSAGE)

    assert error.value.code == "llm_timeout"
    assert error.value.status_code == 504


@pytest.mark.parametrize("status_code", [400, 404, 500])
async def test_ollama_error_status_is_reported_without_leaking_the_body(status_code: int) -> None:
    provider = _ollama(lambda _: httpx.Response(status_code, json={"error": "model not found"}))

    with pytest.raises(ExternalServiceError) as error:
        await provider.chat(USER_MESSAGE)

    assert error.value.code == "llm_request_failed"
    assert error.value.status_code == 502
    assert "model not found" not in error.value.message


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="<html>not json</html>"),
        httpx.Response(200, json={"unexpected": True}),
        httpx.Response(200, json={"model": "m", "message": {"tool_calls": "not-a-list"}}),
        httpx.Response(200, json=["a", "list"]),
    ],
)
async def test_ollama_malformed_response_is_rejected(response: httpx.Response) -> None:
    with pytest.raises(LLMInvalidResponseError) as error:
        await _ollama(lambda _: response).chat(USER_MESSAGE)

    assert error.value.code == "llm_invalid_response"


# --- Ollama: availability ---------------------------------------------------


async def test_ollama_is_available_when_the_version_endpoint_answers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/version"
        return httpx.Response(200, json={"version": "0.5.1"})

    assert await _ollama(handler).is_available() is True


async def test_ollama_is_unavailable_when_unreachable_or_failing() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    assert await _ollama(refuse).is_available() is False
    assert await _ollama(lambda _: httpx.Response(500)).is_available() is False


# --- Mock provider and factory ----------------------------------------------


async def test_mock_replays_its_script_in_order_then_falls_back() -> None:
    calls = [ToolCall(id="c1", name="demo_echo", arguments={"text": "a"})]
    provider = MockLLMProvider(["một", calls])

    first = await provider.chat(USER_MESSAGE)
    second = await provider.chat(USER_MESSAGE)
    third = await provider.chat(USER_MESSAGE)

    assert first.content == "một"
    assert second.tool_calls == calls
    assert third.content == DEFAULT_REPLY
    assert first.provider == "mock"


async def test_mock_raises_scripted_errors_and_records_calls() -> None:
    provider = MockLLMProvider([ExternalServiceUnavailableError()])
    tools = [ToolDefinition(name="demo_echo", description="d", parameters={})]

    with pytest.raises(ExternalServiceUnavailableError):
        await provider.chat(USER_MESSAGE, tools=tools, response_schema={"type": "object"})

    assert len(provider.calls) == 1
    assert provider.calls[0].messages == USER_MESSAGE
    assert provider.calls[0].tools == tools
    assert provider.calls[0].response_schema == {"type": "object"}
    assert await provider.is_available() is True


async def test_factory_builds_the_configured_provider_without_contacting_it() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise AssertionError("the factory must not send requests")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ollama_settings = Settings(
        _env_file=None,
        llm_provider=LLMProviderName.OLLAMA,
        ollama_model="some-model",
    )
    mock_settings = Settings(_env_file=None, llm_provider=LLMProviderName.MOCK)

    ollama = build_llm_provider(ollama_settings, client)
    mock = build_llm_provider(mock_settings, client)

    assert isinstance(ollama, OllamaProvider)
    assert ollama.model == "some-model"
    assert isinstance(mock, MockLLMProvider)
