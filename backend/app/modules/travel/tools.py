"""Travel tools for the assistant. They call the travel services; they hold no rules of their own.

The model knows place names, not coordinates: tools resolve names through
place search. Creating a plan is a proposal the user confirms.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.external import ExternalServices
from app.infrastructure.geo import GeoPlace
from app.infrastructure.weather import WeatherForecast
from app.modules.travel.dependencies import build_plan_service
from app.modules.travel.info import TravelInfoService
from app.modules.travel.schemas import PlanCreate, PlanDetail, PlanOut, TransportOptions
from app.modules.travel.service import TravelPlanService, check_dates
from app.shared.tools import Tool, ToolContext, ToolEffect, ToolSpec

DOMAIN = "travel"

PlaceName = Field(min_length=2, max_length=200, description="Tên địa điểm, ví dụ 'Đà Lạt'.")


class _TravelTool:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], external: ExternalServices
    ) -> None:
        self._session_factory = session_factory
        self._info = TravelInfoService(external)

    @asynccontextmanager
    async def _plans(self) -> AsyncIterator[TravelPlanService]:
        async with self._session_factory() as session:
            yield build_plan_service(session)


# --- Places ------------------------------------------------------------------


class SearchPlacesInput(BaseModel):
    query: str = PlaceName
    limit: int = Field(default=5, ge=1, le=10)


class PlaceList(BaseModel):
    places: list[GeoPlace]
    source: str = "© OpenStreetMap contributors"


class SearchPlacesTool(_TravelTool, Tool[SearchPlacesInput, PlaceList]):
    spec = ToolSpec(
        name="travel_search_places",
        description="Tìm địa điểm trên OpenStreetMap theo tên hoặc địa chỉ.",
        domain=DOMAIN,
        effect=ToolEffect.READ,
        input_model=SearchPlacesInput,
        output_model=PlaceList,
    )

    async def execute(self, context: ToolContext, tool_input: SearchPlacesInput) -> PlaceList:
        return PlaceList(
            places=await self._info.search_places(tool_input.query, limit=tool_input.limit)
        )


# --- Weather -----------------------------------------------------------------


class WeatherInput(BaseModel):
    place: str = PlaceName
    days: int = Field(default=3, ge=1, le=16, description="Số ngày dự báo.")


class PlaceWeather(BaseModel):
    place: str
    forecast: WeatherForecast


class GetWeatherTool(_TravelTool, Tool[WeatherInput, PlaceWeather]):
    spec = ToolSpec(
        name="travel_get_weather",
        description="Thời tiết hiện tại và dự báo theo ngày của một địa điểm (Open-Meteo).",
        domain=DOMAIN,
        effect=ToolEffect.READ,
        input_model=WeatherInput,
        output_model=PlaceWeather,
    )

    async def execute(self, context: ToolContext, tool_input: WeatherInput) -> PlaceWeather:
        place = await self._info.resolve_place(tool_input.place)
        forecast = await self._info.weather(place.lat, place.lon, days=tool_input.days)
        return PlaceWeather(place=place.name, forecast=forecast)


# --- Transport ---------------------------------------------------------------


class TransportInput(BaseModel):
    origin: str = PlaceName
    destination: str = PlaceName
    travel_date: date = Field(description="Ngày đi, YYYY-MM-DD.")
    adults: int = Field(default=1, ge=1, le=9)


class FindTransportTool(_TravelTool, Tool[TransportInput, TransportOptions]):
    spec = ToolSpec(
        name="travel_find_transport",
        description=(
            "Cách đi giữa hai địa điểm: quãng đường và thời gian lái xe, giá vé máy bay nếu có, "
            "và trang đặt vé tàu, xe khách. Atlas không có giờ tàu, giờ xe: chỉ đưa liên kết."
        ),
        domain=DOMAIN,
        effect=ToolEffect.READ,
        input_model=TransportInput,
        output_model=TransportOptions,
    )

    async def execute(self, context: ToolContext, tool_input: TransportInput) -> TransportOptions:
        origin = await self._info.resolve_place(tool_input.origin)
        destination = await self._info.resolve_place(tool_input.destination)
        return await self._info.transport(
            origin, destination, tool_input.travel_date, adults=tool_input.adults
        )


# --- Plans -------------------------------------------------------------------


class ListPlansInput(BaseModel):
    pass


class PlanList(BaseModel):
    plans: list[PlanOut]
    total: int


class ListPlansTool(_TravelTool, Tool[ListPlansInput, PlanList]):
    spec = ToolSpec(
        name="travel_list_plans",
        description="Các kế hoạch du lịch đã lưu của người dùng.",
        domain=DOMAIN,
        effect=ToolEffect.READ,
        input_model=ListPlansInput,
        output_model=PlanList,
    )

    async def execute(self, context: ToolContext, tool_input: ListPlansInput) -> PlanList:
        async with self._plans() as plans:
            page = await plans.list_plans(context.user_id, limit=20)
        return PlanList(plans=page.items, total=page.total)


class CreatePlanInput(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    destination: str | None = Field(default=None, min_length=2, max_length=200)
    start_date: date | None = Field(default=None, description="YYYY-MM-DD")
    end_date: date | None = Field(default=None, description="YYYY-MM-DD")
    note: str | None = Field(default=None, max_length=2000)


class CreatePlanTool(_TravelTool, Tool[CreatePlanInput, PlanDetail]):
    spec = ToolSpec(
        name="travel_create_plan",
        description=(
            "Đề xuất tạo một kế hoạch du lịch. Không lưu ngay: người dùng phải bấm xác nhận."
        ),
        domain=DOMAIN,
        effect=ToolEffect.WRITE,
        input_model=CreatePlanInput,
        output_model=PlanDetail,
    )

    async def preview(self, context: ToolContext, tool_input: CreatePlanInput) -> str:
        check_dates(tool_input.start_date, tool_input.end_date)
        parts = [f"Tạo kế hoạch '{tool_input.title}'"]
        if tool_input.destination:
            place = await self._info.resolve_place(tool_input.destination)
            parts.append(f"điểm đến {place.name}")
        if tool_input.start_date:
            parts.append(f"từ {tool_input.start_date.strftime('%d/%m/%Y')}")
        if tool_input.end_date:
            parts.append(f"đến {tool_input.end_date.strftime('%d/%m/%Y')}")
        return ", ".join(parts) + "."

    async def execute(self, context: ToolContext, tool_input: CreatePlanInput) -> PlanDetail:
        destination = (
            await self._info.resolve_place(tool_input.destination)
            if tool_input.destination
            else None
        )
        async with self._plans() as plans:
            return await plans.create_plan(
                context.user_id,
                PlanCreate(
                    title=tool_input.title,
                    destination=destination,
                    start_date=tool_input.start_date,
                    end_date=tool_input.end_date,
                    note=tool_input.note,
                ),
            )


def build_travel_tools(
    session_factory: async_sessionmaker[AsyncSession], external: ExternalServices
) -> list[Tool[BaseModel, BaseModel]]:
    tools: list[Tool[BaseModel, BaseModel]] = [
        SearchPlacesTool(session_factory, external),  # type: ignore[list-item]
        GetWeatherTool(session_factory, external),  # type: ignore[list-item]
        FindTransportTool(session_factory, external),  # type: ignore[list-item]
        ListPlansTool(session_factory, external),  # type: ignore[list-item]
        CreatePlanTool(session_factory, external),  # type: ignore[list-item]
    ]
    return tools
