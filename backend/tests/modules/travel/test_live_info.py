"""Places, weather and transport endpoints. External services are in-memory fakes."""

from typing import Any

import httpx
import pytest

from app.core.exceptions import ExternalServiceTimeoutError, ExternalServiceUnavailableError
from tests.travel_support import DA_LAT, HANOI, FakeExternal, flight_offer

HANOI_TO_DA_LAT: dict[str, Any] = {
    "origin_name": "Hà Nội",
    "origin_lat": HANOI.lat,
    "origin_lon": HANOI.lon,
    "destination_name": "Đà Lạt",
    "destination_lat": DA_LAT.lat,
    "destination_lon": DA_LAT.lon,
    "travel_date": "2026-12-01",
}


async def _transport(client: httpx.AsyncClient, **params: Any) -> dict[str, Any]:
    response = await client.get("/api/v1/travel/transport", params={**HANOI_TO_DA_LAT, **params})
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


# --- Places and weather ------------------------------------------------------


async def test_place_search_returns_matches(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    response = await client.get("/api/v1/places/search", params={"q": " Đà Lạt ", "limit": 3})

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Đà Lạt"
    assert external.places.queries == ["Đà Lạt"]


@pytest.mark.parametrize("params", [{"q": "a"}, {"q": "x" * 201}, {"q": "Huế", "limit": 11}, {}])
async def test_place_search_validates_the_query(
    client: httpx.AsyncClient, params: dict[str, Any]
) -> None:
    response = await client.get("/api/v1/places/search", params=params)
    assert response.status_code == 422


async def test_place_search_failure_is_a_502_with_a_clear_code(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    external.places.error = ExternalServiceUnavailableError(
        "Mất kết nối.", code="nominatim_unavailable"
    )

    response = await client.get("/api/v1/places/search", params={"q": "Huế"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "nominatim_unavailable"


async def test_weather_returns_current_and_daily_forecast(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    response = await client.get(
        "/api/v1/travel/weather", params={"lat": 11.94, "lon": 108.45, "days": 3}
    )

    body = response.json()
    assert response.status_code == 200
    assert body["current"]["description"] == "Có mây"
    assert len(body["daily"]) == 3
    assert body["source"] == "Weather data by Open-Meteo.com"
    assert external.weather.requests == [(11.94, 108.45, 3)]


@pytest.mark.parametrize(
    "params",
    [{"lat": 91, "lon": 0}, {"lat": 0, "lon": 181}, {"lat": 0, "lon": 0, "days": 17}, {"lat": 0}],
)
async def test_weather_validates_coordinates(
    client: httpx.AsyncClient, params: dict[str, Any]
) -> None:
    assert (await client.get("/api/v1/travel/weather", params=params)).status_code == 422


async def test_weather_timeout_is_a_504(client: httpx.AsyncClient, external: FakeExternal) -> None:
    external.weather.error = ExternalServiceTimeoutError("Chậm.", code="open_meteo_timeout")
    response = await client.get("/api/v1/travel/weather", params={"lat": 1, "lon": 1})
    assert response.status_code == 504


# --- Transport ---------------------------------------------------------------


async def test_transport_combines_road_flights_and_booking_links(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    external.flights.offers = [
        flight_offer(1_900_000),
        flight_offer(None),
        flight_offer(1_250_000, stops=1),
    ]

    body = await _transport(client, adults=2)

    assert body["road"] == {
        "status": "ok",
        "distance_km": 1480.2,
        "duration_minutes": 1500,
        "message": None,
    }
    flights = body["flights"]
    assert flights["status"] == "ok"
    assert (flights["origin_airport"], flights["destination_airport"]) == ("HAN", "DLI")
    assert [offer["price_vnd"] for offer in flights["offers"]] == [1_250_000, 1_900_000, None]
    assert flights["source"] == "Google Flights qua SerpApi"
    assert external.flights.searches[0][3] == 2
    assert {link["mode"] for link in body["ground_links"]} == {"train", "bus"}
    assert body["straight_distance_km"] > 1000


async def test_without_a_serpapi_key_flights_offer_a_google_flights_link(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    external.flights.enabled = False

    flights = (await _transport(client))["flights"]

    assert flights["status"] == "not_configured"
    assert flights["offers"] == []
    assert flights["search_url"].startswith("https://www.google.com/travel/flights")
    assert external.flights.searches == []


async def test_nearby_places_do_not_suggest_flights(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    flights = (
        await _transport(
            client, destination_name="Bắc Ninh", destination_lat=21.1861, destination_lon=106.0763
        )
    )["flights"]

    assert flights["status"] == "too_close"
    assert external.flights.searches == []


async def test_a_place_far_from_any_airport_reports_no_airport(client: httpx.AsyncClient) -> None:
    # The middle of the South China Sea, more than 150 km from every listed airport.
    flights = (await _transport(client, destination_lat=14.5, destination_lon=113.5))["flights"]
    assert flights["status"] == "no_airport"
    assert flights["search_url"] is None


async def test_airport_codes_given_by_the_user_take_precedence(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    await _transport(client, origin_airport="vii", destination_airport="SGN")
    assert external.flights.searches[0][:2] == ("VII", "SGN")


async def test_one_failing_provider_does_not_hide_the_others(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    external.roads.error = ExternalServiceTimeoutError("Chậm.", code="osrm_timeout")
    external.flights.error = ExternalServiceUnavailableError("Lỗi.", code="serpapi_unavailable")

    body = await _transport(client)

    assert body["road"]["status"] == "unavailable"
    assert body["flights"]["status"] == "unavailable"
    assert body["flights"]["search_url"] is not None
    assert len(body["ground_links"]) == 2


async def test_no_road_between_the_places(
    client: httpx.AsyncClient, external: FakeExternal
) -> None:
    external.roads.route_result = None
    assert (await _transport(client))["road"]["status"] == "no_route"


@pytest.mark.parametrize(
    "override",
    [
        {"travel_date": "01/12/2026"},
        {"adults": 0},
        {"adults": 10},
        {"origin_airport": "HA1"},
        {"origin_lat": 95},
    ],
)
async def test_transport_validates_parameters(
    client: httpx.AsyncClient, override: dict[str, Any]
) -> None:
    response = await client.get("/api/v1/travel/transport", params={**HANOI_TO_DA_LAT, **override})
    assert response.status_code == 422
