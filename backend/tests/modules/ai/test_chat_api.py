"""POST /api/v1/chat through the full HTTP stack, with a scripted model."""

import uuid
from collections.abc import AsyncIterator, Callable, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from typing import Any

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.exceptions import ExternalServiceTimeoutError, ExternalServiceUnavailableError
from app.main import create_app
from app.modules.ai.providers.base import ToolCall
from app.modules.ai.providers.mock import DEFAULT_REPLY, MockLLMProvider
from app.modules.memory.models import Message
from app.shared.tools import Tool
from tests.ai_support import EchoTool, SaveNoteTool, build_runtime, tool_call
from tests.database import remove_default_user

Script = Sequence[str | list[ToolCall] | Exception]
ClientFactory = Callable[..., AbstractAsyncContextManager[httpx.AsyncClient]]


@pytest.fixture
def chat_client(settings: Settings) -> ClientFactory:
    """Build a client for an app whose model follows `script`."""

    @asynccontextmanager
    async def factory(
        script: Script = (), tools: Sequence[Tool[Any, Any]] = ()
    ) -> AsyncIterator[httpx.AsyncClient]:
        app = create_app(settings)
        app.state.ai_runtime = build_runtime(MockLLMProvider(script), tools)
        async with app.router.lifespan_context(app):
            transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                client.app = app  # type: ignore[attr-defined]
                yield client

    return factory


async def _message_count(client: httpx.AsyncClient) -> int:
    factory: async_sessionmaker[AsyncSession] = client.app.state.session_factory  # type: ignore[attr-defined]
    async with factory() as session:
        return await session.scalar(select(func.count()).select_from(Message)) or 0


async def test_chat_returns_the_reply_and_conversation_identifiers(
    chat_client: ClientFactory,
) -> None:
    async with chat_client(["Chào bạn!"]) as client:
        response = await client.post("/api/v1/chat", json={"message": "Xin chào"})

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Chào bạn!"
    assert body["intent"] == "general"
    assert body["tool_calls"] == []
    assert uuid.UUID(body["conversation_id"])
    assert uuid.UUID(body["message_id"])


async def test_chat_continues_an_existing_conversation(chat_client: ClientFactory) -> None:
    async with chat_client(["một", "hai"]) as client:
        first = (await client.post("/api/v1/chat", json={"message": "a"})).json()
        second = await client.post(
            "/api/v1/chat", json={"message": "b", "conversation_id": first["conversation_id"]}
        )

        assert second.status_code == 200
        assert second.json()["conversation_id"] == first["conversation_id"]
        assert second.json()["reply"] == "hai"
        assert await _message_count(client) == 4


async def test_chat_reports_the_tools_that_were_used(chat_client: ClientFactory) -> None:
    script = ['{"intent": "demo"}', [tool_call("demo_echo", text="a")], "a"]

    async with chat_client(script, [EchoTool()]) as client:
        response = await client.post("/api/v1/chat", json={"message": "Lặp lại a"})

    assert response.status_code == 200
    assert response.json()["intent"] == "demo"
    assert response.json()["tool_calls"] == [{"name": "demo_echo", "status": "success"}]


async def test_chat_works_with_the_default_mock_provider(client: httpx.AsyncClient) -> None:
    """The application answers without any LLM service when LLM_PROVIDER=mock."""
    response = await client.post("/api/v1/chat", json={"message": "Xin chào"})

    assert response.status_code == 200
    assert response.json()["reply"] == DEFAULT_REPLY


async def test_chat_trims_the_message(chat_client: ClientFactory) -> None:
    provider_script = ["ok"]
    async with chat_client(provider_script) as client:
        await client.post("/api/v1/chat", json={"message": "  Xin chào  "})
        provider: MockLLMProvider = client.app.state.ai_runtime.provider  # type: ignore[attr-defined]

    assert provider.calls[0].messages[-1].content == "Xin chào"


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({}, "message"),
        ({"message": ""}, "message"),
        ({"message": "   "}, "message"),
        ({"message": "x" * 4001}, "message"),
        ({"message": 5}, "message"),
        ({"message": "ok", "conversation_id": "not-a-uuid"}, "conversation_id"),
    ],
)
async def test_chat_rejects_invalid_requests_without_calling_the_model(
    chat_client: ClientFactory, payload: dict[str, object], field: str
) -> None:
    async with chat_client() as client:
        response = await client.post("/api/v1/chat", json=payload)
        provider: MockLLMProvider = client.app.state.ai_runtime.provider  # type: ignore[attr-defined]

        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "validation_error"
        assert error["details"][0]["field"] == field
        assert provider.calls == []
        assert await _message_count(client) == 0


async def test_chat_validation_message_is_shown_without_library_prefixes(
    chat_client: ClientFactory,
) -> None:
    async with chat_client() as client:
        response = await client.post("/api/v1/chat", json={"message": "   "})

    assert response.json()["error"]["details"][0]["message"] == "Tin nhắn không được để trống."


async def test_chat_accepts_a_message_at_the_maximum_length(chat_client: ClientFactory) -> None:
    async with chat_client(["ok"]) as client:
        response = await client.post("/api/v1/chat", json={"message": "x" * 4000})

    assert response.status_code == 200


async def test_chat_returns_404_for_an_unknown_conversation(chat_client: ClientFactory) -> None:
    async with chat_client() as client:
        response = await client.post(
            "/api/v1/chat", json={"message": "Chào", "conversation_id": str(uuid.uuid4())}
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "conversation_not_found"


@pytest.mark.parametrize(
    ("failure", "status_code", "code"),
    [
        (ExternalServiceUnavailableError(code="llm_unavailable"), 503, "llm_unavailable"),
        (ExternalServiceTimeoutError(code="llm_timeout"), 504, "llm_timeout"),
    ],
)
async def test_chat_reports_provider_failures_and_keeps_the_user_message(
    chat_client: ClientFactory, failure: Exception, status_code: int, code: str
) -> None:
    async with chat_client([failure]) as client:
        response = await client.post("/api/v1/chat", json={"message": "Chào"})

        assert response.status_code == status_code
        error = response.json()["error"]
        assert error["code"] == code
        assert error["request_id"] == response.headers["X-Request-ID"]
        assert await _message_count(client) == 1


async def test_chat_reports_a_missing_default_user(chat_client: ClientFactory) -> None:
    async with chat_client() as client:
        factory: async_sessionmaker[AsyncSession] = client.app.state.session_factory  # type: ignore[attr-defined]
        async with factory() as session:
            await remove_default_user(session)
            await session.commit()

        response = await client.post("/api/v1/chat", json={"message": "Chào"})

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "default_user_missing"


async def test_proposed_change_is_confirmed_through_the_api(chat_client: ClientFactory) -> None:
    tool = SaveNoteTool()
    script = [
        '{"intent": "demo"}',
        [tool_call("demo_save_note", text="mua sữa")],
        "Bạn xác nhận nhé.",
    ]

    async with chat_client(script, [tool]) as client:
        chat = (await client.post("/api/v1/chat", json={"message": "Ghi chú mua sữa"})).json()
        proposal = chat["pending_actions"][0]
        assert chat["tool_calls"] == [{"name": "demo_save_note", "status": "pending"}]
        assert proposal["summary"] == "Lưu ghi chú: mua sữa"
        assert proposal["status"] == "pending"
        assert tool.saved == []

        confirmed = await client.post(f"/api/v1/chat/actions/{proposal['id']}/confirm")
        again = await client.post(f"/api/v1/chat/actions/{proposal['id']}/cancel")

    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
    assert tool.saved == ["mua sữa"]
    assert (again.status_code, again.json()["error"]["code"]) == (409, "pending_action_resolved")


async def test_unknown_action_returns_404(chat_client: ClientFactory) -> None:
    async with chat_client() as client:
        response = await client.post(f"/api/v1/chat/actions/{uuid.uuid4()}/confirm")

    assert (response.status_code, response.json()["error"]["code"]) == (
        404,
        "pending_action_not_found",
    )
