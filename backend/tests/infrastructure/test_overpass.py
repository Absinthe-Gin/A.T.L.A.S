"""Overpass (OpenStreetMap restaurants) adapter, tested against `httpx.MockTransport`."""

from collections.abc import Callable
from urllib.parse import parse_qs

import httpx
import pytest

from app.core.exceptions import ExternalServiceError, ExternalServiceTimeoutError
from app.infrastructure.geo import GeoPoint
from app.infrastructure.overpass import OverpassRestaurants, build_query

HANOI = GeoPoint(lat=21.0285, lon=105.8542)
Handler = Callable[[httpx.Request], httpx.Response]


def _adapter(client: httpx.AsyncClient) -> OverpassRestaurants:
    return OverpassRestaurants(
        client,
        base_url="https://overpass.test/api/interpreter",
        timeout_seconds=5,
        user_agent="ATLAS-Test/1",
    )


def _client(handler: Handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_query_searches_restaurants_by_name_around_the_point() -> None:
    query = build_query(HANOI, ["phở", "pho"], 5000, 10)

    assert '"name"~"phở|pho",i' in query
    assert "(around:5000,21.0285,105.8542)" in query
    assert query.endswith("out center 10;")


@pytest.mark.parametrize("term", ['x"]; out; (', "<script>", "bún;bò", ""])
def test_unsafe_search_terms_never_reach_the_query(term: str) -> None:
    with pytest.raises(ValueError):
        build_query(HANOI, [term], 5000, 10)


async def test_parses_nodes_and_ways_and_skips_unnamed_elements() -> None:
    payload = {
        "elements": [
            {
                "type": "node",
                "id": 1,
                "lat": 21.03,
                "lon": 105.85,
                "tags": {
                    "name": "Phở Thìn",
                    "cuisine": "vietnamese",
                    "addr:street": "Lò Đúc",
                    "addr:housenumber": "13",
                    "opening_hours": "06:00-22:00",
                },
            },
            {
                "type": "way",
                "id": 2,
                "center": {"lat": 21.04, "lon": 105.86},
                "tags": {"name": "Bún chả Hương Liên", "contact:website": "https://example.test"},
            },
            {"type": "node", "id": 3, "lat": 21.0, "lon": 105.0, "tags": {"amenity": "cafe"}},
            {"type": "node", "id": 4, "tags": {"name": "Không có tọa độ"}},
        ]
    }
    async with _client(lambda request: httpx.Response(200, json=payload)) as client:
        found = await _adapter(client).search(HANOI, name_terms=["phở"], radius_m=5000, limit=10)

    assert [item.name for item in found] == ["Phở Thìn", "Bún chả Hương Liên"]
    assert found[0].address == "13, Lò Đúc"
    assert found[0].opening_hours == "06:00-22:00"
    assert found[1].lat == pytest.approx(21.04)
    assert found[1].website == "https://example.test"


async def test_request_is_a_form_post_with_an_identifying_user_agent() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"elements": []})

    async with _client(handler) as client:
        await _adapter(client).search(HANOI, name_terms=["bún bò"], radius_m=3000, limit=5)

    request = seen[0]
    assert request.method == "POST"
    assert request.headers["User-Agent"] == "ATLAS-Test/1"
    body = parse_qs(request.content.decode())["data"][0]
    assert '"name"~"bún bò",i' in body


async def test_repeated_search_is_served_from_cache() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"elements": []})

    async with _client(handler) as client:
        adapter = _adapter(client)
        await adapter.search(HANOI, name_terms=["phở"], radius_m=5000, limit=10)
        await adapter.search(
            GeoPoint(lat=21.02851, lon=105.85421), name_terms=["Phở"], radius_m=5000, limit=10
        )

    assert len(calls) == 1


async def test_radius_and_limit_are_clamped_to_safe_bounds() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(parse_qs(request.content.decode())["data"][0])
        return httpx.Response(200, json={"elements": []})

    async with _client(handler) as client:
        await _adapter(client).search(HANOI, name_terms=["phở"], radius_m=10**9, limit=10**6)

    assert "(around:20000," in seen[0]
    assert seen[0].endswith("out center 20;")


async def test_payload_without_elements_is_an_invalid_response() -> None:
    async with _client(
        lambda request: httpx.Response(200, json={"remark": "runtime error"})
    ) as client:
        with pytest.raises(ExternalServiceError) as caught:
            await _adapter(client).search(HANOI, name_terms=["phở"], radius_m=5000, limit=10)
    assert caught.value.code == "overpass_invalid"


async def test_server_errors_and_timeouts_are_mapped_to_service_errors() -> None:
    async with _client(lambda request: httpx.Response(504)) as client:
        with pytest.raises(ExternalServiceError) as caught:
            await _adapter(client).search(HANOI, name_terms=["phở"], radius_m=5000, limit=10)
    assert caught.value.code == "overpass_error"

    def slow(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    async with _client(slow) as client:
        with pytest.raises(ExternalServiceTimeoutError) as caught:
            await _adapter(client).search(HANOI, name_terms=["phở"], radius_m=5000, limit=10)
    assert caught.value.code == "overpass_timeout"
