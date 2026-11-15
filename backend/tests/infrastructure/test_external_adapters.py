"""Adapters to free external services, tested against `httpx.MockTransport`."""

import json
import logging
import time
from collections.abc import Callable
from datetime import date

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import (
    ExternalServiceError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)
from app.infrastructure.external import user_agent
from app.infrastructure.flights import SerpApiFlights, google_flights_url
from app.infrastructure.geo import GeoPoint, NominatimGeocoder, OsrmRouter, distance_km
from app.infrastructure.http.fetch import TtlCache, get_json
from app.infrastructure.weather import OpenMeteoWeather, describe_weather

Handler = Callable[[httpx.Request], httpx.Response]


def client_for(handler: Handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


# --- get_json ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("handler", "error_type", "code"),
    [
        (lambda request: httpx.Response(500), ExternalServiceError, "demo_error"),
        (
            lambda request: httpx.Response(200, content=b"not json"),
            ExternalServiceError,
            "demo_invalid",
        ),
    ],
)
async def test_get_json_maps_bad_responses_to_service_errors(
    handler: Handler, error_type: type[ExternalServiceError], code: str
) -> None:
    async with client_for(handler) as client:
        with pytest.raises(error_type) as caught:
            await get_json(client, "https://example.test/x", service="demo", timeout_seconds=1)
    assert caught.value.code == code


async def test_get_json_maps_timeouts_and_network_failures() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    def offline(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    async with client_for(timeout) as client:
        with pytest.raises(ExternalServiceTimeoutError):
            await get_json(client, "https://example.test/x", service="demo", timeout_seconds=1)
    async with client_for(offline) as client:
        with pytest.raises(ExternalServiceUnavailableError) as caught:
            await get_json(client, "https://example.test/x", service="demo", timeout_seconds=1)
    assert caught.value.code == "demo_unavailable"


async def test_errors_never_carry_the_request_url_with_its_api_key(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async with client_for(lambda request: httpx.Response(401)) as client:
        with caplog.at_level(logging.DEBUG), pytest.raises(ExternalServiceError) as caught:
            await get_json(
                client,
                "https://example.test/x",
                service="demo",
                params={"api_key": "s3cret"},
                timeout_seconds=1,
            )
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__
    assert "s3cret" not in str(caught.value)
    assert "s3cret" not in caplog.text


def test_ttl_cache_expires_and_evicts() -> None:
    now = [0.0]
    cache: TtlCache[str, int] = TtlCache(ttl_seconds=10, max_entries=2, clock=lambda: now[0])
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert cache.get("a") is None
    assert cache.get("b") == 2
    now[0] = 11
    assert cache.get("b") is None


# --- Nominatim ---------------------------------------------------------------


NOMINATIM_RESULT = [
    {
        "lat": "11.9404",
        "lon": "108.4583",
        "display_name": "Đà Lạt, Lâm Đồng, Việt Nam",
        "name": "Đà Lạt",
        "category": "boundary",
        "type": "administrative",
        "osm_type": "relation",
        "osm_id": 1906245,
    },
    {"lat": "not-a-number", "lon": "1", "display_name": "Broken"},
    {"lat": "12.0", "lon": "108.0", "display_name": "Chợ Đà Lạt, Đà Lạt"},
]


async def test_nominatim_search_parses_results_and_identifies_the_application() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=NOMINATIM_RESULT)

    async with client_for(handler) as client:
        geocoder = NominatimGeocoder(
            client, base_url="https://nominatim.test", user_agent="ATLAS-Test/1", timeout_seconds=1
        )
        places = await geocoder.search("Đà Lạt", limit=3)

    assert [p.name for p in places] == ["Đà Lạt", "Chợ Đà Lạt"]
    assert places[0].lat == pytest.approx(11.9404)
    request = seen[0]
    assert request.url.path == "/search"
    assert request.url.params["format"] == "jsonv2"
    assert request.url.params["limit"] == "3"
    assert request.headers["User-Agent"] == "ATLAS-Test/1"


async def test_nominatim_repeated_search_is_served_from_cache() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=NOMINATIM_RESULT)

    async with client_for(handler) as client:
        geocoder = NominatimGeocoder(
            client, base_url="https://nominatim.test", user_agent="t", timeout_seconds=1
        )
        await geocoder.search("Đà Lạt")
        await geocoder.search("  đà lạt ")

    assert len(calls) == 1


async def test_nominatim_waits_between_requests() -> None:
    async with client_for(lambda request: httpx.Response(200, json=[])) as client:
        geocoder = NominatimGeocoder(
            client,
            base_url="https://nominatim.test",
            user_agent="t",
            timeout_seconds=1,
            min_interval_seconds=0.2,
        )
        started = time.monotonic()
        await geocoder.search("a")
        await geocoder.search("b")
    assert time.monotonic() - started >= 0.19


async def test_nominatim_rejects_a_non_list_payload() -> None:
    async with client_for(lambda request: httpx.Response(200, json={"error": "x"})) as client:
        geocoder = NominatimGeocoder(
            client, base_url="https://n.test", user_agent="t", timeout_seconds=1
        )
        with pytest.raises(ExternalServiceError):
            await geocoder.search("x")


def test_user_agent_names_the_contact_only_when_configured() -> None:
    assert "self-hosted)" in user_agent(Settings(_env_file=None))
    with_contact = Settings(_env_file=None, osm_contact="me@example.org")
    assert user_agent(with_contact).endswith("(self-hosted; me@example.org)")


# --- OSRM --------------------------------------------------------------------


async def test_osrm_returns_distance_and_duration() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200, json={"code": "Ok", "routes": [{"distance": 1480234.0, "duration": 90000.0}]}
        )

    async with client_for(handler) as client:
        router = OsrmRouter(client, base_url="https://osrm.test", user_agent="t", timeout_seconds=1)
        route = await router.route(GeoPoint(lat=21.0, lon=105.8), GeoPoint(lat=11.9, lon=108.4))

    assert route is not None
    assert route.distance_km == 1480.2
    assert route.duration_minutes == 1500
    # OSRM takes longitude first.
    assert seen[0].url.path == "/route/v1/driving/105.8,21.0;108.4,11.9"


async def test_osrm_without_a_route_returns_none() -> None:
    async with client_for(lambda request: httpx.Response(200, json={"code": "NoRoute"})) as client:
        router = OsrmRouter(client, base_url="https://osrm.test", user_agent="t", timeout_seconds=1)
        assert await router.route(GeoPoint(lat=0, lon=0), GeoPoint(lat=1, lon=1)) is None


def test_distance_km_between_hanoi_and_ho_chi_minh_city() -> None:
    assert distance_km(
        GeoPoint(lat=21.0285, lon=105.8542), GeoPoint(lat=10.7769, lon=106.7009)
    ) == (pytest.approx(1140, abs=10))


# --- Open-Meteo --------------------------------------------------------------


OPEN_METEO_RESULT = {
    "latitude": 11.94,
    "longitude": 108.46,
    "timezone": "Asia/Ho_Chi_Minh",
    "current": {
        "time": "2026-12-01T09:00",
        "temperature_2m": 18.4,
        "relative_humidity_2m": 81,
        "apparent_temperature": 17.6,
        "precipitation": 0.0,
        "weather_code": 3,
        "wind_speed_10m": 6.5,
    },
    "daily": {
        "time": ["2026-12-01", "2026-12-02"],
        "weather_code": [3, 61],
        "temperature_2m_max": [22.1, 21.0],
        "temperature_2m_min": [14.3, 15.0],
        "precipitation_probability_max": [10, 70],
    },
}


async def test_open_meteo_forecast_is_parsed_and_described_in_vietnamese() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=OPEN_METEO_RESULT)

    async with client_for(handler) as client:
        weather = OpenMeteoWeather(client, base_url="https://meteo.test", timeout_seconds=1)
        forecast = await weather.forecast(11.94, 108.46, days=2)
        await weather.forecast(11.94, 108.46, days=2)

    assert len(seen) == 1, "the second call is cached"
    assert seen[0].url.params["timezone"] == "auto"
    assert forecast.current.description == "Nhiều mây"
    assert [day.description for day in forecast.daily] == ["Nhiều mây", "Mưa nhỏ"]
    assert forecast.daily[1].precipitation_probability_percent == 70


async def test_open_meteo_missing_fields_are_a_service_error() -> None:
    async with client_for(lambda request: httpx.Response(200, json={"latitude": 1})) as client:
        weather = OpenMeteoWeather(client, base_url="https://meteo.test", timeout_seconds=1)
        with pytest.raises(ExternalServiceError) as caught:
            await weather.forecast(1, 1)
    assert caught.value.code == "open_meteo_invalid"


def test_unknown_weather_code_is_described_as_unknown() -> None:
    assert describe_weather(1234) == "Không rõ"


# --- SerpApi -----------------------------------------------------------------


def _segment(number: str) -> dict[str, object]:
    return {
        "airline": "Vietjet",
        "flight_number": number,
        "departure_airport": {"id": "HAN", "time": "2026-12-01 06:00"},
        "arrival_airport": {"id": "DLI", "time": "2026-12-01 08:00"},
        "duration": 120,
    }


async def test_serpapi_offers_are_parsed_from_best_and_other_flights() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "best_flights": [
                    {"flights": [_segment("VJ 1")], "total_duration": 120, "price": 1250000}
                ],
                "other_flights": [
                    {"flights": [_segment("VJ 2"), _segment("VJ 3")], "price": 990000},
                    {"flights": "malformed"},
                ],
            },
        )

    async with client_for(handler) as client:
        flights = SerpApiFlights(
            client, base_url="https://serp.test", api_key=SecretStr("k"), timeout_seconds=1
        )
        offers = await flights.search("HAN", "DLI", date(2026, 12, 1), adults=2)

    assert [(o.price_vnd, o.stops) for o in offers] == [(1250000, 0), (990000, 1)]
    params = seen[0].url.params
    assert params["engine"] == "google_flights"
    assert params["type"] == "2"
    assert params["currency"] == "VND"
    assert params["adults"] == "2"


async def test_serpapi_no_results_is_an_empty_answer() -> None:
    body = json.dumps({"error": "Google Flights hasn't returned any results for this query."})
    async with client_for(lambda request: httpx.Response(200, content=body)) as client:
        flights = SerpApiFlights(
            client, base_url="https://serp.test", api_key=SecretStr("k"), timeout_seconds=1
        )
        assert await flights.search("HAN", "DLI", date(2026, 12, 1)) == []


async def test_serpapi_other_errors_are_service_errors() -> None:
    async with client_for(
        lambda request: httpx.Response(200, json={"error": "Invalid API key."})
    ) as client:
        flights = SerpApiFlights(
            client, base_url="https://serp.test", api_key=SecretStr("k"), timeout_seconds=1
        )
        with pytest.raises(ExternalServiceError) as caught:
            await flights.search("HAN", "DLI", date(2026, 12, 1))
    assert caught.value.code == "serpapi_error"


def test_serpapi_is_disabled_without_a_key() -> None:
    flights = SerpApiFlights(
        httpx.AsyncClient(), base_url="https://serp.test", api_key=SecretStr(""), timeout_seconds=1
    )
    assert not flights.enabled


def test_google_flights_url_names_the_route_and_date() -> None:
    url = google_flights_url("HAN", "DLI", date(2026, 12, 1))
    assert url.startswith("https://www.google.com/travel/flights?q=")
    assert "HAN" in url and "DLI" in url and "2026-12-01" in url
