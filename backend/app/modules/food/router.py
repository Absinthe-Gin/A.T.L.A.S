from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.infrastructure.geo import GeoPoint
from app.modules.food.dependencies import get_food_service
from app.modules.food.schemas import DishSearchResult, RegionRecommendation
from app.modules.food.service import FoodService

Service = Annotated[FoodService, Depends(get_food_service)]
Latitude = Annotated[float, Query(ge=-90, le=90)]
Longitude = Annotated[float, Query(ge=-180, le=180)]

router = APIRouter(tags=["food"])


@router.get("/food/recommendations", response_model=RegionRecommendation)
async def recommend(lat: Latitude, lon: Longitude, service: Service) -> RegionRecommendation:
    """Specialties of the region nearest to the given point. No external call."""
    return service.recommend(GeoPoint(lat=lat, lon=lon))


@router.get("/food/restaurants", response_model=DishSearchResult)
async def find_restaurants(
    service: Service,
    dish: Annotated[str, Query(min_length=2, max_length=120)],
    lat: Latitude,
    lon: Longitude,
    radius_m: Annotated[int, Query(ge=100, le=20000)] = 5000,
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
) -> DishSearchResult:
    """Restaurants whose name contains the dish, nearest first (OpenStreetMap)."""
    return await service.search_dish(
        dish, GeoPoint(lat=lat, lon=lon), radius_m=radius_m, limit=limit
    )
