"""Photon adapters and provider fallback, tested against `httpx.MockTransport`."""

from collections.abc import Callable, Sequence

import httpx
import pytest

from app.core.config import Settings
from app.core.exceptions import ExternalServiceError, ExternalServiceUnavailableError
from app.infrastructure.external import build_external_services
from app.infrastructure.fallback import FallbackPlaceSearch, FallbackRestaurantSearch
from app.infrastructure.geo import GeoPlace, GeoPoint
from app.infrastructure.overpass import Restaurant
from app.infrastructure.photon import PhotonGeocoder, PhotonRestaurants, fold

HANOI = GeoPoint(lat=21.0285, lon=105.8542)
Handler = Callable[[httpx.Request], httpx.Response]


def _client(handler: Handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _feature(
    name: str | None, lat: float, lon: float, osm_id: int = 1, **props: object
) -> dict[str, object]:
    properties: dict[str, object] = {"osm_type": "N", "osm_id": osm_id, **props}
    if name is not None:
        properties["name"] = name
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": properties,
    }


def test_fold_ignores_case_and_vietnamese_diacritics() -> None:
    assert fold("Phở Cường") == "pho cuong"
    assert fold("ĐẬU") == "dau"


# --- Places ------------------------------------------------------------------


async def test_geocoder_parses_places_and_biases_towards_the_given_point() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "features": [
                    _feature(
                        "Huế",
                        16.4637,
                        107.5909,
                        osm_key="place",
                        osm_value="city",
                        country="Việt Nam",
                    ),
                    _feature(None, 1, 1),
                    {"broken": True},
                ]
            },
        )

    async with _client(handler) as client:
        geocoder = PhotonGeocoder(
            client,
            base_url="https://photon.test",
            user_agent="ATLAS-Test/1",
            timeout_seconds=1,
            bias=GeoPoint(lat=16.0, lon=106.5),
        )
        places = await geocoder.search("Huế", limit=3)

    assert [(p.name, p.type, p.osm_type) for p in places] == [("Huế", "city", "node")]
    assert places[0].display_name == "Huế, Việt Nam"
    params = seen[0].url.params
    assert (params["q"], params["lat"], params["lon"], params["limit"]) == (
        "Huế",
        "16.0",
        "106.5",
        "3",
    )
    assert seen[0].headers["User-Agent"] == "ATLAS-Test/1"


async def test_geocoder_rejects_a_payload_without_features() -> None:
    async with _client(lambda request: httpx.Response(200, json={"message": "x"})) as client:
        geocoder = PhotonGeocoder(
            client, base_url="https://photon.test", user_agent="t", timeout_seconds=1
        )
        with pytest.raises(ExternalServiceError) as caught:
            await geocoder.search("x")
    assert caught.value.code == "photon_invalid"


# --- Restaurants -------------------------------------------------------------


async def test_restaurants_are_filtered_by_name_and_radius_and_sorted_by_distance() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "features": [
                    _feature("Phở Xa", 21.10, 105.85, osm_id=1),  # about 8 km away
                    _feature(
                        "Phở Cường",
                        21.0300,
                        105.8550,
                        osm_id=2,
                        street="Phố Hàng Muối",
                        city="Hà Nội",
                    ),
                    _feature("Bún chả", 21.0290, 105.8545, osm_id=3),  # wrong dish
                    _feature("Pho Thin", 21.0350, 105.8540, osm_id=4),  # no diacritics
                ]
            },
        )

    async with _client(handler) as client:
        adapter = PhotonRestaurants(
            client, base_url="https://photon.test", user_agent="t", timeout_seconds=1
        )
        found = await adapter.search(HANOI, name_terms=["phở"], radius_m=3000, limit=10)

    assert [r.name for r in found] == ["Phở Cường", "Pho Thin"]
    assert found[0].address == "Phố Hàng Muối, Hà Nội"
    assert found[0].opening_hours is None, "Photon has no opening hours; never guessed"
    params = seen[0].url.params
    assert params.get_list("osm_tag") == ["amenity:restaurant", "amenity:fast_food", "amenity:cafe"]
    assert (params["lat"], params["lon"]) == ("21.0285", "105.8542")


async def test_each_term_is_searched_and_duplicates_are_merged() -> None:
    queries: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        queries.append(request.url.params["q"])
        return httpx.Response(
            200, json={"features": [_feature("Phở Cường", 21.03, 105.855, osm_id=2)]}
        )

    async with _client(handler) as client:
        adapter = PhotonRestaurants(
            client, base_url="https://photon.test", user_agent="t", timeout_seconds=1
        )
        found = await adapter.search(
            HANOI, name_terms=["phở", "pho", "Phở"], radius_m=5000, limit=10
        )
        await adapter.search(HANOI, name_terms=["phở", "pho"], radius_m=5000, limit=10)

    assert queries == ["phở", "pho"], "duplicate terms are dropped and the repeat is cached"
    assert len(found) == 1


async def test_limit_keeps_the_nearest_restaurants() -> None:
    features = [_feature(f"Phở {i}", 21.0285 + i / 1000, 105.8542, osm_id=i) for i in range(1, 6)]
    async with _client(lambda request: httpx.Response(200, json={"features": features})) as client:
        adapter = PhotonRestaurants(
            client, base_url="https://photon.test", user_agent="t", timeout_seconds=1
        )
        found = await adapter.search(HANOI, name_terms=["phở"], radius_m=5000, limit=2)

    assert [r.name for r in found] == ["Phở 1", "Phở 2"]


# --- Fallback ----------------------------------------------------------------


class _Places:
    def __init__(
        self, result: list[GeoPlace] | None = None, error: ExternalServiceError | None = None
    ):
        self.result = result or []
        self.error = error
        self.calls = 0

    async def search(self, query: str, *, limit: int = 5) -> list[GeoPlace]:
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


class _Restaurants:
    def __init__(
        self, result: list[Restaurant] | None = None, error: ExternalServiceError | None = None
    ):
        self.result = result or []
        self.error = error
        self.calls = 0

    async def search(
        self, point: GeoPoint, *, name_terms: Sequence[str], radius_m: int, limit: int
    ) -> list[Restaurant]:
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


HUE = GeoPlace(name="Huế", display_name="Huế", lat=16.46, lon=107.59)
BLOCKED = ExternalServiceUnavailableError("Không kết nối được.", code="nominatim_unavailable")


async def test_place_search_moves_to_the_next_provider_when_one_fails(
    caplog: pytest.LogCaptureFixture,
) -> None:
    first, second = _Places(error=BLOCKED), _Places([HUE])

    assert await FallbackPlaceSearch([first, second]).search("Huế") == [HUE]
    assert "Place search provider failed" in caplog.text


async def test_an_empty_answer_is_not_a_failure() -> None:
    first, second = _Places([]), _Places([HUE])

    assert await FallbackPlaceSearch([first, second]).search("không có") == []
    assert second.calls == 0


async def test_when_every_provider_fails_the_last_error_is_raised() -> None:
    last = ExternalServiceError("Lỗi.", code="photon_error")

    with pytest.raises(ExternalServiceError) as caught:
        await FallbackPlaceSearch([_Places(error=BLOCKED), _Places(error=last)]).search("x")
    assert caught.value.code == "photon_error"


async def test_restaurant_search_moves_to_the_next_provider_when_one_fails() -> None:
    restaurant = Restaurant(osm_type="node", osm_id=1, name="Phở", lat=21.03, lon=105.85)
    first = _Restaurants(error=ExternalServiceError("Lỗi.", code="photon_error"))
    second = _Restaurants([restaurant])

    found = await FallbackRestaurantSearch([first, second]).search(
        HANOI, name_terms=["phở"], radius_m=1000, limit=5
    )

    assert found == [restaurant]
    assert (first.calls, second.calls) == (1, 1)


def test_fallback_needs_at_least_one_provider() -> None:
    with pytest.raises(ValueError):
        FallbackPlaceSearch([])


async def test_the_application_wires_a_second_provider_for_places_and_restaurants() -> None:
    async with httpx.AsyncClient() as client:
        services = build_external_services(Settings(_env_file=None), client)

    assert isinstance(services.places, FallbackPlaceSearch)
    assert isinstance(services.restaurants, FallbackRestaurantSearch)
