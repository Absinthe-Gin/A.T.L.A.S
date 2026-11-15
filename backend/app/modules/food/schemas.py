from typing import Literal

from pydantic import BaseModel

from app.infrastructure.overpass import ATTRIBUTION as RESTAURANT_SOURCE


class DishSuggestion(BaseModel):
    name: str
    description: str


class RegionRecommendation(BaseModel):
    """Specialties of the region nearest to the user. Editorial suggestions, not statistics."""

    region: str
    reference_city: str
    distance_to_reference_km: float
    dishes: list[DishSuggestion]
    note: str


class RestaurantOut(BaseModel):
    name: str
    cuisine: str | None
    address: str | None
    opening_hours: str | None
    phone: str | None
    website: str | None
    lat: float
    lon: float
    distance_km: float
    osm_type: str
    osm_id: int


DishSearchStatus = Literal["ok", "no_results", "unavailable"]


class DishSearchResult(BaseModel):
    """Restaurants whose name contains the dish, nearest first."""

    dish: str
    radius_m: int
    status: DishSearchStatus
    restaurants: list[RestaurantOut]
    message: str | None
    source: str = RESTAURANT_SOURCE
