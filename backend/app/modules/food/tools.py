"""Food tools for the assistant. They call FoodService; they hold no rules of their own."""

from pydantic import BaseModel, Field

from app.infrastructure.external import ExternalServices
from app.infrastructure.geo import GeoPoint
from app.modules.food.schemas import DishSearchResult, RegionRecommendation
from app.modules.food.service import FoodService
from app.shared.tools import Tool, ToolContext, ToolEffect, ToolSpec

DOMAIN = "food"


class _FoodTool:
    def __init__(self, external: ExternalServices) -> None:
        self._service = FoodService(external)


class RecommendInput(BaseModel):
    place: str = Field(
        min_length=2, max_length=200, description="Khu vực hoặc thành phố, ví dụ 'Huế'."
    )


class RecommendTool(_FoodTool, Tool[RecommendInput, RegionRecommendation]):
    spec = ToolSpec(
        name="food_recommend_dishes",
        description="Món đặc sản của miền gần địa điểm người dùng nêu.",
        domain=DOMAIN,
        effect=ToolEffect.READ,
        input_model=RecommendInput,
        output_model=RegionRecommendation,
    )

    async def execute(
        self, context: ToolContext, tool_input: RecommendInput
    ) -> RegionRecommendation:
        place = await self._service.resolve_place(tool_input.place)
        return self._service.recommend(GeoPoint(lat=place.lat, lon=place.lon))


class FindRestaurantsInput(BaseModel):
    dish: str = Field(min_length=2, max_length=80, description="Tên món, ví dụ 'bún bò'.")
    place: str = Field(
        min_length=2, max_length=200, description="Khu vực tìm quán, ví dụ 'Hà Nội'."
    )
    radius_km: float = Field(default=5, gt=0, le=20, description="Bán kính tìm, km.")


class FindRestaurantsTool(_FoodTool, Tool[FindRestaurantsInput, DishSearchResult]):
    spec = ToolSpec(
        name="food_find_restaurants",
        description=(
            "Tìm quán có tên chứa món ăn quanh một địa điểm, gần nhất trước (OpenStreetMap). "
            "Kết quả chỉ gồm quán đã được ghi nhận trong dữ liệu."
        ),
        domain=DOMAIN,
        effect=ToolEffect.READ,
        input_model=FindRestaurantsInput,
        output_model=DishSearchResult,
    )

    async def execute(
        self, context: ToolContext, tool_input: FindRestaurantsInput
    ) -> DishSearchResult:
        place = await self._service.resolve_place(tool_input.place)
        return await self._service.search_dish(
            tool_input.dish,
            GeoPoint(lat=place.lat, lon=place.lon),
            radius_m=round(tool_input.radius_km * 1000),
        )


def build_food_tools(external: ExternalServices) -> list[Tool[BaseModel, BaseModel]]:
    tools: list[Tool[BaseModel, BaseModel]] = [
        RecommendTool(external),  # type: ignore[list-item]
        FindRestaurantsTool(external),  # type: ignore[list-item]
    ]
    return tools
