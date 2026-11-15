import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.infrastructure.geo import GeoPlace
from app.infrastructure.weather import WeatherForecast
from app.modules.travel.dependencies import get_info_service, get_plan_service
from app.modules.travel.info import TravelInfoService
from app.modules.travel.schemas import (
    ItemCreate,
    ItemOut,
    ItemUpdate,
    PlaceRef,
    PlanCreate,
    PlanDetail,
    PlanOut,
    PlanUpdate,
    TransportOptions,
)
from app.modules.travel.service import TravelPlanService
from app.modules.users.public import CurrentUser, get_current_user
from app.shared.schemas import Page

User = Annotated[CurrentUser, Depends(get_current_user)]
Plans = Annotated[TravelPlanService, Depends(get_plan_service)]
Info = Annotated[TravelInfoService, Depends(get_info_service)]
Latitude = Annotated[float, Query(ge=-90, le=90)]
Longitude = Annotated[float, Query(ge=-180, le=180)]
AirportCode = Annotated[
    str | None, Query(pattern=r"^[A-Za-z]{3}$", description="Mã IATA, ví dụ HAN")
]

router = APIRouter(tags=["travel"])


# --- Plans -------------------------------------------------------------------


@router.get("/travel/plans", response_model=Page[PlanOut])
async def list_plans(
    user: User,
    plans: Plans,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Page[PlanOut]:
    return await plans.list_plans(user.id, limit=limit, offset=offset)


@router.post("/travel/plans", response_model=PlanDetail, status_code=status.HTTP_201_CREATED)
async def create_plan(payload: PlanCreate, user: User, plans: Plans) -> PlanDetail:
    return await plans.create_plan(user.id, payload)


@router.get("/travel/plans/{plan_id}", response_model=PlanDetail)
async def get_plan(plan_id: uuid.UUID, user: User, plans: Plans) -> PlanDetail:
    return await plans.get_plan(user.id, plan_id)


@router.patch("/travel/plans/{plan_id}", response_model=PlanDetail)
async def update_plan(
    plan_id: uuid.UUID, payload: PlanUpdate, user: User, plans: Plans
) -> PlanDetail:
    return await plans.update_plan(user.id, plan_id, payload)


@router.delete("/travel/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(plan_id: uuid.UUID, user: User, plans: Plans) -> Response:
    await plans.delete_plan(user.id, plan_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/travel/plans/{plan_id}/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED
)
async def add_item(plan_id: uuid.UUID, payload: ItemCreate, user: User, plans: Plans) -> ItemOut:
    return await plans.add_item(user.id, plan_id, payload)


@router.patch("/travel/plans/{plan_id}/items/{item_id}", response_model=ItemOut)
async def update_item(
    plan_id: uuid.UUID, item_id: uuid.UUID, payload: ItemUpdate, user: User, plans: Plans
) -> ItemOut:
    return await plans.update_item(user.id, plan_id, item_id, payload)


@router.delete("/travel/plans/{plan_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(plan_id: uuid.UUID, item_id: uuid.UUID, user: User, plans: Plans) -> Response:
    await plans.delete_item(user.id, plan_id, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Live information --------------------------------------------------------


@router.get("/places/search", response_model=list[GeoPlace])
async def search_places(
    info: Info,
    q: Annotated[str, Query(min_length=2, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
) -> list[GeoPlace]:
    """Places on OpenStreetMap (© OpenStreetMap contributors)."""
    return await info.search_places(q.strip(), limit=limit)


@router.get("/travel/weather", response_model=WeatherForecast)
async def weather(
    info: Info, lat: Latitude, lon: Longitude, days: Annotated[int, Query(ge=1, le=16)] = 7
) -> WeatherForecast:
    """Current weather and daily forecast (Open-Meteo)."""
    return await info.weather(lat, lon, days=days)


@router.get("/travel/transport", response_model=TransportOptions)
async def transport(
    info: Info,
    origin_name: Annotated[str, Query(min_length=1, max_length=200)],
    origin_lat: Latitude,
    origin_lon: Longitude,
    destination_name: Annotated[str, Query(min_length=1, max_length=200)],
    destination_lat: Latitude,
    destination_lon: Longitude,
    travel_date: date,
    adults: Annotated[int, Query(ge=1, le=9)] = 1,
    origin_airport: AirportCode = None,
    destination_airport: AirportCode = None,
) -> TransportOptions:
    """Road distance, flight offers when available, and train/coach booking sites."""
    return await info.transport(
        PlaceRef(name=origin_name, lat=origin_lat, lon=origin_lon),
        PlaceRef(name=destination_name, lat=destination_lat, lon=destination_lon),
        travel_date,
        adults=adults,
        origin_airport=origin_airport,
        destination_airport=destination_airport,
    )
