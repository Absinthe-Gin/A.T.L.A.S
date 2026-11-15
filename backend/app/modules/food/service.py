"""Food use cases: regional suggestions and restaurant search. Holds no HTTP details."""

import logging
import re

from app.core.exceptions import ExternalServiceError
from app.infrastructure.external import ExternalServices
from app.infrastructure.geo import GeoPlace, GeoPoint, distance_km
from app.modules.food.catalog import REGIONS, Dish, Region
from app.modules.food.exceptions import FoodPlaceNotFoundError, InvalidDishQueryError
from app.modules.food.schemas import (
    DishSearchResult,
    DishSuggestion,
    RegionRecommendation,
    RestaurantOut,
)

logger = logging.getLogger(__name__)

DEFAULT_RADIUS_M = 5000
MAX_DISH_LENGTH = 80
NOTE = (
    "Gợi ý biên tập của Atlas, dựa trên món đặc trưng của vùng. "
    "Không phải số liệu thống kê về độ phổ biến."
)


def clean_dish_query(text: str) -> str:
    """Trim and check a dish name. Only letters, digits, spaces and hyphens are allowed."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not 2 <= len(cleaned) <= MAX_DISH_LENGTH:
        raise InvalidDishQueryError(f"Tên món phải có từ 2 đến {MAX_DISH_LENGTH} ký tự.")
    if not all(char.isalnum() or char in " -" for char in cleaned):
        raise InvalidDishQueryError()
    return cleaned


def nearest_region(point: GeoPoint) -> tuple[Region, float]:
    return min(
        ((region, distance_km(point, region.center)) for region in REGIONS),
        key=lambda pair: pair[1],
    )


class FoodService:
    def __init__(self, external: ExternalServices) -> None:
        self._external = external

    async def resolve_place(self, name: str) -> GeoPlace:
        """Best match for a place name, for callers that only have a name (the assistant)."""
        places = await self._external.places.search(name.strip(), limit=1)
        if not places:
            raise FoodPlaceNotFoundError(f"Không tìm thấy địa điểm '{name}'.")
        return places[0]

    def recommend(self, point: GeoPoint) -> RegionRecommendation:
        region, distance = nearest_region(point)
        return RegionRecommendation(
            region=region.name,
            reference_city=region.reference_city,
            distance_to_reference_km=round(distance, 1),
            dishes=[
                DishSuggestion(name=dish.name, description=dish.description)
                for dish in region.dishes
            ],
            note=NOTE,
        )

    async def search_dish(
        self, dish: str, point: GeoPoint, *, radius_m: int = DEFAULT_RADIUS_M, limit: int = 10
    ) -> DishSearchResult:
        name = clean_dish_query(dish)
        return await self._search(name, [name], point, radius_m=radius_m, limit=limit)

    async def search_region_dish(
        self, dish: Dish, point: GeoPoint, *, radius_m: int = DEFAULT_RADIUS_M, limit: int = 10
    ) -> DishSearchResult:
        return await self._search(
            dish.name, list(dish.search_terms), point, radius_m=radius_m, limit=limit
        )

    async def _search(
        self, label: str, terms: list[str], point: GeoPoint, *, radius_m: int, limit: int
    ) -> DishSearchResult:
        try:
            found = await self._external.restaurants.search(
                point, name_terms=terms, radius_m=radius_m, limit=limit
            )
        except ExternalServiceError as error:
            logger.warning("Restaurant search failed", extra={"error_code": error.code})
            return DishSearchResult(
                dish=label,
                radius_m=radius_m,
                status="unavailable",
                restaurants=[],
                message="Chưa tìm được quán ăn lúc này. Thử lại sau.",
            )

        restaurants = sorted(
            (
                RestaurantOut(
                    name=item.name,
                    cuisine=item.cuisine,
                    address=item.address,
                    opening_hours=item.opening_hours,
                    phone=item.phone,
                    website=item.website,
                    lat=item.lat,
                    lon=item.lon,
                    distance_km=round(distance_km(point, GeoPoint(lat=item.lat, lon=item.lon)), 2),
                    osm_type=item.osm_type,
                    osm_id=item.osm_id,
                )
                for item in found
            ),
            key=lambda item: item.distance_km,
        )[:limit]
        if not restaurants:
            return DishSearchResult(
                dish=label,
                radius_m=radius_m,
                status="no_results",
                restaurants=[],
                message=(
                    f"Không có quán nào có tên chứa '{label}' trong bán kính "
                    f"{radius_m / 1000:g} km trên OpenStreetMap. Thử tăng bán kính, "
                    "hoặc dữ liệu chưa được ghi nhận."
                ),
            )
        return DishSearchResult(
            dish=label, radius_m=radius_m, status="ok", restaurants=restaurants, message=None
        )
