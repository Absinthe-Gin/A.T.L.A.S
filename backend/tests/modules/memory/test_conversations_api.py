"""Conversation history endpoints (list, read, rename, delete) and a conversation's proposals."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.models import PendingAction
from app.modules.ai.providers.mock import MockLLMProvider
from app.modules.memory.models import Message
from tests.ai_support import SaveNoteTool, build_runtime, tool_call


def _use_script(app: FastAPI, script: list[Any]) -> None:
    app.state.ai_runtime = build_runtime(MockLLMProvider(script), [SaveNoteTool()])


async def _chat(
    client: httpx.AsyncClient, text: str, conversation_id: str | None = None
) -> dict[str, Any]:
    response = await client.post(
        "/api/v1/chat", json={"message": text, "conversation_id": conversation_id}
    )
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


async def _set_message_time(session: AsyncSession, conversation_id: str, when: datetime) -> None:
    """Make the order of activity deterministic (clock resolution varies between systems)."""
    await session.execute(
        update(Message)
        .where(Message.conversation_id == uuid.UUID(conversation_id))
        .values(created_at=when)
    )
    await session.commit()


async def test_an_empty_history_is_an_empty_page(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/conversations")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "limit": 30, "offset": 0}


async def test_conversations_are_listed_by_last_activity_with_their_title(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession
) -> None:
    _use_script(app, ["Chào bạn", "Đây là kế hoạch", "Ok"])
    first = await _chat(client, "Xin chào Atlas")
    second = await _chat(client, "Lập kế hoạch đi Huế")
    now = datetime.now(UTC)
    await _set_message_time(session, second["conversation_id"], now - timedelta(hours=2))
    await _set_message_time(session, first["conversation_id"], now - timedelta(hours=1))

    page = (await client.get("/api/v1/conversations")).json()

    assert page["total"] == 2
    assert [item["id"] for item in page["items"]] == [
        first["conversation_id"],
        second["conversation_id"],
    ]
    assert page["items"][0]["title"] == "Xin chào Atlas"

    second_page = (
        await client.get("/api/v1/conversations", params={"limit": 1, "offset": 1})
    ).json()
    assert [item["id"] for item in second_page["items"]] == [second["conversation_id"]]


async def test_messages_are_newest_first_without_internal_tool_steps(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession
) -> None:
    _use_script(
        app,
        ['{"intent": "demo"}', [tool_call("demo_save_note", text="mua sữa")], "Bạn xác nhận nhé."],
    )
    reply = await _chat(client, "Ghi chú giúp mình")
    conversation_id = reply["conversation_id"]
    stored = await session.scalar(
        select(func.count())
        .select_from(Message)
        .where(Message.conversation_id == uuid.UUID(conversation_id))
    )

    page = (await client.get(f"/api/v1/conversations/{conversation_id}/messages")).json()

    assert stored == 4, "user, assistant tool call, tool result, assistant reply are all stored"
    assert [(m["role"], m["content"]) for m in page["items"]] == [
        ("assistant", "Bạn xác nhận nhé."),
        ("user", "Ghi chú giúp mình"),
    ]
    assert page["total"] == 2


async def test_unknown_conversation_is_not_found(client: httpx.AsyncClient) -> None:
    missing = uuid.uuid4()

    for response in [
        await client.get(f"/api/v1/conversations/{missing}/messages"),
        await client.patch(f"/api/v1/conversations/{missing}", json={"title": "A"}),
        await client.delete(f"/api/v1/conversations/{missing}"),
    ]:
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "conversation_not_found"


async def test_rename_trims_the_title(app: FastAPI, client: httpx.AsyncClient) -> None:
    _use_script(app, ["Chào"])
    conversation_id = (await _chat(client, "Xin chào"))["conversation_id"]

    response = await client.patch(
        f"/api/v1/conversations/{conversation_id}", json={"title": "  Chuyến Huế  "}
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Chuyến Huế"
    listed = (await client.get("/api/v1/conversations")).json()["items"]
    assert listed[0]["title"] == "Chuyến Huế"


@pytest.mark.parametrize("title", ["", "   ", "x" * 201])
async def test_rename_rejects_blank_or_long_titles(
    app: FastAPI, client: httpx.AsyncClient, title: str
) -> None:
    _use_script(app, ["Chào"])
    conversation_id = (await _chat(client, "Xin chào"))["conversation_id"]

    response = await client.patch(f"/api/v1/conversations/{conversation_id}", json={"title": title})

    assert response.status_code == 422


async def test_delete_removes_messages_and_proposals(
    app: FastAPI, client: httpx.AsyncClient, session: AsyncSession
) -> None:
    _use_script(
        app,
        ['{"intent": "demo"}', [tool_call("demo_save_note", text="mua sữa")], "Bạn xác nhận nhé."],
    )
    conversation_id = (await _chat(client, "Ghi chú giúp mình"))["conversation_id"]

    response = await client.delete(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 204
    assert (
        await client.get(f"/api/v1/conversations/{conversation_id}/messages")
    ).status_code == 404
    remaining_messages = await session.scalar(select(func.count()).select_from(Message))
    remaining_actions = await session.scalar(select(func.count()).select_from(PendingAction))
    assert (remaining_messages, remaining_actions) == (0, 0)


async def test_proposals_of_a_conversation_can_be_listed_and_confirmed_later(
    app: FastAPI, client: httpx.AsyncClient
) -> None:
    _use_script(
        app,
        ['{"intent": "demo"}', [tool_call("demo_save_note", text="mua sữa")], "Bạn xác nhận nhé."],
    )
    conversation_id = (await _chat(client, "Ghi chú giúp mình"))["conversation_id"]

    actions = (await client.get(f"/api/v1/chat/conversations/{conversation_id}/actions")).json()

    assert [(a["tool_name"], a["status"]) for a in actions] == [("demo_save_note", "pending")]
    assert actions[0]["created_at"] is not None
    confirmed = await client.post(f"/api/v1/chat/actions/{actions[0]['id']}/confirm")
    assert confirmed.json()["status"] == "confirmed"
    again = (await client.get(f"/api/v1/chat/conversations/{conversation_id}/actions")).json()
    assert again[0]["status"] == "confirmed"


async def test_a_conversation_without_proposals_lists_none(client: httpx.AsyncClient) -> None:
    response = await client.get(f"/api/v1/chat/conversations/{uuid.uuid4()}/actions")

    assert response.status_code == 200
    assert response.json() == []
