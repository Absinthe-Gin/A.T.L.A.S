"""Food: regional suggestions, dish search through the HTTP stack, and the assistant's tools."""

import uuid

import httpx
import pytest
from fastapi import FastAPI

from app.core.exceptions import ExternalServiceUnavailableError
from app.infrastructure.geo import GeoPoint
from app.infrastructure.overpass import Restaurant
from app.modules.food.catalog import REGIONS
from app.modules.food.exceptions import InvalidDishQueryError
from app.modules.food.schemas import DishSearchResult, RegionRecommendation
from app.modules.food.service import FoodService, clean_dish_query
from app.modules.food.tools import FindRestaurantsInput, RecommendInput, build_food_tools
from app.modules.users.models import DEFAULT_USER_ID
from app.shared.tools import ToolContext, ToolEffect
from tests.travel_support import FakeExternal, place

CONTEXT = ToolContext(user_id=DEFAULT_USER_ID, conversation_id=uuid.uuid4())
HANOI_CENTER = GeoPoint(lat=21.0285, lon=105.8542)


def _restaurant(name: str, lat: float, lon: float, osm_id: int = 1) -> Restaurant:
    return Restaurant(osm_type="node", osm_id=osm_id, name=name, lat=lat, lon=lon)


# --- Suggestions -------------------------------------------------------------


@pytest.mark.parametrize(
    ("point", "region"),
    [
        (GeoPoint(lat=21.03, lon=105.85), "Miền Bắc"),
        (GeoPoint(lat=16.06, lon=108.22), "Miền Trung"),
        (GeoPoint(lat=10.78, lon=106.70), "Miền Nam"),
    ],
)
def test_the_nearest_region_supplies_its_specialties(point: GeoPoint, region: str) -> None:
    service = FoodService(FakeExternal().services)

    suggestion = service.recommend(point)

    assert suggestion.region == region
    assert len(suggestion.dishes) == 4
    assert "biên tập" in suggestion.note
    assert suggestion.distance_to_reference_km < 50


def test_every_region_has_dishes_with_search_terms() -> None:
    for region in REGIONS:
        assert len(region.dishes) == 4
        assert all(dish.search_terms for dish in region.dishes)


@pytest.mark.parametrize(
    "text",
    ["x", "a;b", "bún<bò>", "phở ' or 1=1", '"quoted"', "a" * 81],
)
def test_dish_queries_with_symbols_or_bad_length_are_rejected(text: str) -> None:
    with pytest.raises(InvalidDishQueryError):
        clean_dish_query(text)


def test_dish_query_is_trimmed_and_keeps_vietnamese_letters() -> None:
    assert clean_dish_query("  bún   bò  ") == "bún bò"
    assert clean_dish_query("cơm-tấm") == "cơm-tấm"


# --- HTTP ---------------------------------------------------------------------


async def test_recommendations_endpoint_needs_no_external_service(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    response = await client.get(
        "/api/v1/food/recommendations", params={"lat": 16.06, "lon": 108.22}
    )

    body = response.json()
    assert response.status_code == 200
    assert body["region"] == "Miền Trung"
    assert body["reference_city"] == "Đà Nẵng"
    assert body["dishes"][0]["name"] == "Bún bò Huế"
    assert external.restaurants.searches == []


async def test_restaurants_are_listed_nearest_first_with_distance(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    external.restaurants.restaurants = [
        _restaurant("Phở Xa", 21.10, 105.85, osm_id=1),
        _restaurant("Phở Gần", 21.0300, 105.8550, osm_id=2),
    ]

    response = await client.get(
        "/api/v1/food/restaurants",
        params={"dish": "phở", "lat": HANOI_CENTER.lat, "lon": HANOI_CENTER.lon},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ok"
    assert [item["name"] for item in body["restaurants"]] == ["Phở Gần", "Phở Xa"]
    assert body["restaurants"][0]["distance_km"] < body["restaurants"][1]["distance_km"]
    assert body["restaurants"][0]["distance_km"] < 1
    assert body["source"].startswith("© OpenStreetMap contributors")
    assert external.restaurants.searches[0][0] == ("phở",)
    assert external.restaurants.searches[0][3] == 5000


async def test_limit_keeps_only_the_nearest_restaurants(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    external.restaurants.restaurants = [
        _restaurant(f"Quán {i}", 21.0285 + i / 1000, 105.8542, i) for i in range(5)
    ]

    body = (
        await client.get(
            "/api/v1/food/restaurants",
            params={"dish": "bún", "lat": HANOI_CENTER.lat, "lon": HANOI_CENTER.lon, "limit": 2},
        )
    ).json()

    assert [item["name"] for item in body["restaurants"]] == ["Quán 0", "Quán 1"]


async def test_no_matching_restaurant_is_an_explicit_empty_status(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    body = (
        await client.get(
            "/api/v1/food/restaurants",
            params={"dish": "bánh mì", "lat": HANOI_CENTER.lat, "lon": HANOI_CENTER.lon},
        )
    ).json()

    assert body["status"] == "no_results"
    assert body["restaurants"] == []
    assert "bánh mì" in body["message"]


async def test_provider_failure_is_reported_without_failing_the_request(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    external.restaurants.error = ExternalServiceUnavailableError(
        "Lỗi.", code="overpass_unavailable"
    )

    response = await client.get(
        "/api/v1/food/restaurants",
        params={"dish": "phở", "lat": HANOI_CENTER.lat, "lon": HANOI_CENTER.lon},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"


async def test_unsafe_dish_text_is_rejected_by_the_api(client: httpx.AsyncClient) -> None:
    response = await client.get(
        "/api/v1/food/restaurants", params={"dish": 'phở"]; out;', "lat": 21, "lon": 105}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_dish_query"


@pytest.mark.parametrize("params", [{"lat": 91, "lon": 0}, {"lat": 0, "lon": 0, "radius_m": 50}])
async def test_coordinates_and_radius_are_validated(
    client: httpx.AsyncClient, params: dict[str, float]
) -> None:
    response = await client.get("/api/v1/food/restaurants", params={"dish": "phở", **params})
    assert response.status_code == 422


async def test_region_dish_uses_its_search_terms(external: FakeExternal, app: FastAPI) -> None:
    service = FoodService(external.services)
    dish = REGIONS[0].dishes[0]

    await service.search_region_dish(dish, HANOI_CENTER)

    assert external.restaurants.searches[0][0] == dish.search_terms


# --- Assistant tools -----------------------------------------------------------


def test_food_tools_are_read_only_and_named_by_domain(external: FakeExternal) -> None:
    tools = {tool.spec.name: tool.spec.effect for tool in build_food_tools(external.services)}

    assert tools == {
        "food_recommend_dishes": ToolEffect.READ,
        "food_find_restaurants": ToolEffect.READ,
    }


async def test_recommend_tool_resolves_the_place_name(external: FakeExternal) -> None:
    external.places.places["huế"] = [place("Huế", 16.4637, 107.5909)]
    tool = build_food_tools(external.services)[0]

    result = await tool.execute(CONTEXT, RecommendInput(place="Huế"))

    assert isinstance(result, RegionRecommendation) and result.region == "Miền Trung"


async def test_find_tool_converts_km_to_metres(external: FakeExternal) -> None:
    tool = build_food_tools(external.services)[1]

    result = await tool.execute(
        CONTEXT, FindRestaurantsInput(dish="bún bò", place="Hà Nội", radius_km=3)
    )

    assert isinstance(result, DishSearchResult) and result.radius_m == 3000
    assert external.restaurants.searches[-1][3] == 3000


def test_tool_inputs_reject_empty_dish_names() -> None:
    with pytest.raises(ValueError):
        FindRestaurantsInput(dish="", place="Hà Nội")
