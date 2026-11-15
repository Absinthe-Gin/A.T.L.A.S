"""Travel tools: what the assistant can read and propose."""

import uuid
from collections.abc import AsyncIterator
from datetime import date

import httpx
import pytest
from fastapi import FastAPI
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.ai.providers.base import ToolCall
from app.modules.ai.providers.mock import MockLLMProvider
from app.modules.travel.exceptions import InvalidDateRangeError, PlaceNotFoundError
from app.modules.travel.tools import (
    CreatePlanInput,
    CreatePlanTool,
    FindTransportTool,
    GetWeatherTool,
    ListPlansInput,
    ListPlansTool,
    TransportInput,
    WeatherInput,
    build_travel_tools,
)
from app.modules.users.models import DEFAULT_USER_ID
from app.shared.tools import ToolContext, ToolEffect
from tests.ai_support import build_runtime, tool_call
from tests.travel_support import FakeExternal

CONTEXT = ToolContext(user_id=DEFAULT_USER_ID, conversation_id=uuid.uuid4())


@pytest.fixture
def factory(app: FastAPI) -> async_sessionmaker[AsyncSession]:
    return app.state.session_factory  # type: ignore[no-any-return]


def test_only_the_create_tool_writes(
    factory: async_sessionmaker[AsyncSession], external: FakeExternal
) -> None:
    tools = {
        tool.spec.name: tool.spec.effect for tool in build_travel_tools(factory, external.services)
    }

    assert tools == {
        "travel_search_places": ToolEffect.READ,
        "travel_get_weather": ToolEffect.READ,
        "travel_find_transport": ToolEffect.READ,
        "travel_list_plans": ToolEffect.READ,
        "travel_create_plan": ToolEffect.WRITE,
    }


async def test_weather_tool_resolves_the_place_name(
    factory: async_sessionmaker[AsyncSession], external: FakeExternal
) -> None:
    result = await GetWeatherTool(factory, external.services).execute(
        CONTEXT, WeatherInput(place="Đà Lạt", days=2)
    )

    assert result.place == "Đà Lạt"
    assert external.weather.requests == [(11.9404, 108.4583, 2)]


async def test_unknown_place_is_an_error_the_model_can_fix(
    factory: async_sessionmaker[AsyncSession], external: FakeExternal
) -> None:
    with pytest.raises(PlaceNotFoundError) as caught:
        await GetWeatherTool(factory, external.services).execute(
            CONTEXT, WeatherInput(place="Atlantis")
        )
    assert "Atlantis" in caught.value.message


async def test_transport_tool_finds_ways_between_named_places(
    factory: async_sessionmaker[AsyncSession], external: FakeExternal
) -> None:
    result = await FindTransportTool(factory, external.services).execute(
        CONTEXT,
        TransportInput(origin="Hà Nội", destination="Đà Nẵng", travel_date=date(2026, 12, 1)),
    )

    assert result.destination.name == "Đà Nẵng"
    assert result.flights.destination_airport == "DAD"
    assert result.road.status == "ok"


def test_tool_inputs_are_validated() -> None:
    with pytest.raises(ValidationError):
        WeatherInput(place="x")
    with pytest.raises(ValidationError):
        TransportInput(origin="Hà Nội", destination="Huế", travel_date=date(2026, 1, 1), adults=0)


async def test_create_plan_preview_resolves_the_destination_without_saving(
    factory: async_sessionmaker[AsyncSession], external: FakeExternal
) -> None:
    tool = CreatePlanTool(factory, external.services)

    summary = await tool.preview(
        CONTEXT,
        CreatePlanInput(
            title="Đà Lạt",
            destination="đà lạt",
            start_date=date(2026, 12, 1),
            end_date=date(2026, 12, 3),
        ),
    )

    assert summary == "Tạo kế hoạch 'Đà Lạt', điểm đến Đà Lạt, từ 01/12/2026, đến 03/12/2026."
    listed = await ListPlansTool(factory, external.services).execute(CONTEXT, ListPlansInput())
    assert listed.plans == []


async def test_create_plan_preview_applies_the_date_rule(
    factory: async_sessionmaker[AsyncSession], external: FakeExternal
) -> None:
    with pytest.raises(InvalidDateRangeError):
        await CreatePlanTool(factory, external.services).preview(
            CONTEXT,
            CreatePlanInput(title="A", start_date=date(2026, 12, 3), end_date=date(2026, 12, 1)),
        )


async def test_create_plan_execute_saves_the_plan(
    factory: async_sessionmaker[AsyncSession], external: FakeExternal
) -> None:
    plan = await CreatePlanTool(factory, external.services).execute(
        CONTEXT, CreatePlanInput(title="Đà Nẵng", destination="Đà Nẵng")
    )

    assert plan.destination is not None
    assert plan.destination.lat == pytest.approx(16.0544)
    listed = await ListPlansTool(factory, external.services).execute(CONTEXT, ListPlansInput())
    assert [p.id for p in listed.plans] == [plan.id]


# --- A chat turn -------------------------------------------------------------


@pytest.fixture
async def chat(app: FastAPI, external: FakeExternal) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


async def test_the_assistant_proposes_a_plan_and_the_user_confirms_it(
    app: FastAPI, chat: httpx.AsyncClient, external: FakeExternal
) -> None:
    script: list[str | list[ToolCall] | Exception] = [
        '{"intent": "travel"}',
        [
            tool_call(
                "travel_create_plan", title="Đà Lạt", destination="Đà Lạt", start_date="2026-12-01"
            )
        ],
        "Mình đã chuẩn bị đề xuất, bạn bấm Xác nhận nhé.",
    ]
    app.state.ai_runtime = build_runtime(
        MockLLMProvider(script), build_travel_tools(app.state.session_factory, external.services)
    )

    reply = (
        await chat.post("/api/v1/chat", json={"message": "Lập kế hoạch đi Đà Lạt 1/12"})
    ).json()

    assert reply["intent"] == "travel"
    assert reply["tool_calls"] == [{"name": "travel_create_plan", "status": "pending"}]
    action = reply["pending_actions"][0]
    assert "điểm đến Đà Lạt" in action["summary"]
    assert (await chat.get("/api/v1/travel/plans")).json()["items"] == [], (
        "nothing is saved before confirmation"
    )

    confirmed = await chat.post(f"/api/v1/chat/actions/{action['id']}/confirm")

    assert confirmed.json()["status"] == "confirmed"
    plans = (await chat.get("/api/v1/travel/plans")).json()["items"]
    assert [(p["title"], p["destination"]["name"], p["start_date"]) for p in plans] == [
        ("Đà Lạt", "Đà Lạt", "2026-12-01")
    ]
