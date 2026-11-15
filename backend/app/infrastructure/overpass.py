"""Restaurants from OpenStreetMap through the Overpass API (free, no key).

https://wiki.openstreetmap.org/wiki/Overpass_API

Only restaurants whose OpenStreetMap name contains the searched text are
returned. Coverage depends on what contributors mapped: an empty answer means
"not in the data", not "no such restaurant".
"""

import asyncio
import re
from collections.abc import Sequence
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, ValidationError

from app.core.exceptions import ExternalServiceError
from app.infrastructure.geo import GeoPoint
from app.infrastructure.http.fetch import TtlCache, get_json

ATTRIBUTION = "© OpenStreetMap contributors (Overpass API)"

MAX_RADIUS_M = 20_000
MAX_LIMIT = 20
# A search term may contain letters, digits, spaces and hyphens only. This is what keeps
# user text out of the Overpass query language.
_SAFE_TERM = re.compile(r"^[\w \-]{1,60}$")


class Restaurant(BaseModel):
    osm_type: str
    osm_id: int
    name: str
    lat: float
    lon: float
    cuisine: str | None = None
    address: str | None = None
    opening_hours: str | None = None
    phone: str | None = None
    website: str | None = None


class RestaurantSearch(Protocol):
    async def search(
        self, point: GeoPoint, *, name_terms: Sequence[str], radius_m: int, limit: int
    ) -> list[Restaurant]: ...


class _Element(BaseModel):
    type: str
    id: int
    lat: float | None = None
    lon: float | None = None
    center: dict[str, float] | None = None
    tags: dict[str, str] = {}


def build_query(point: GeoPoint, name_terms: Sequence[str], radius_m: int, limit: int) -> str:
    """The Overpass QL for restaurants whose name matches any term, within `radius_m` metres."""
    for term in name_terms:
        if not _SAFE_TERM.match(term):
            raise ValueError("unsafe search term")
    pattern = "|".join(name_terms)
    return (
        "[out:json][timeout:25];"
        f'nwr["amenity"~"^(restaurant|fast_food|cafe)$"]["name"~"{pattern}",i]'
        f"(around:{radius_m},{point.lat},{point.lon});"
        f"out center {limit};"
    )


def _address(tags: dict[str, str]) -> str | None:
    parts = [tags.get("addr:housenumber"), tags.get("addr:street"), tags.get("addr:city")]
    text = ", ".join(part for part in parts if part)
    return text or None


def _restaurant(element: _Element) -> Restaurant | None:
    tags = element.tags
    name = tags.get("name")
    lat = element.lat if element.lat is not None else (element.center or {}).get("lat")
    lon = element.lon if element.lon is not None else (element.center or {}).get("lon")
    if not name or lat is None or lon is None:
        return None
    return Restaurant(
        osm_type=element.type,
        osm_id=element.id,
        name=name,
        lat=lat,
        lon=lon,
        cuisine=tags.get("cuisine"),
        address=_address(tags),
        opening_hours=tags.get("opening_hours"),
        phone=tags.get("phone") or tags.get("contact:phone"),
        website=tags.get("website") or tags.get("contact:website"),
    )


class OverpassRestaurants:
    """Adapter for the Overpass API. Results are cached for an hour."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        timeout_seconds: float,
        user_agent: str,
        cache: TtlCache[tuple[tuple[str, ...], float, float, int, int], list[Restaurant]]
        | None = None,
    ) -> None:
        self._client = client
        self._url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._headers = {"User-Agent": user_agent}
        self._cache = cache or TtlCache(ttl_seconds=3600)
        # Overpass asks clients not to run queries in parallel; one at a time keeps us polite.
        self._lock = asyncio.Lock()

    async def search(
        self, point: GeoPoint, *, name_terms: Sequence[str], radius_m: int, limit: int
    ) -> list[Restaurant]:
        radius_m = min(max(radius_m, 100), MAX_RADIUS_M)
        limit = min(max(limit, 1), MAX_LIMIT)
        terms = tuple(term.strip().lower() for term in name_terms if term.strip())
        key = (terms, round(point.lat, 3), round(point.lon, 3), radius_m, limit)
        if (cached := self._cache.get(key)) is not None:
            return cached

        query = build_query(point, terms, radius_m, limit)
        async with self._lock:
            payload = await get_json(
                self._client,
                self._url,
                service="overpass",
                form={"data": query},
                headers=self._headers,
                timeout_seconds=self._timeout,
            )
        restaurants = self._parse(payload)
        self._cache.set(key, restaurants)
        return restaurants

    @staticmethod
    def _parse(payload: Any) -> list[Restaurant]:
        if not isinstance(payload, dict) or not isinstance(payload.get("elements"), list):
            raise ExternalServiceError("Dữ liệu quán ăn không hợp lệ.", code="overpass_invalid")
        restaurants: list[Restaurant] = []
        for raw in payload["elements"]:
            try:
                restaurant = _restaurant(_Element.model_validate(raw))
            except ValidationError:
                # One malformed element must not hide the others.
                continue
            if restaurant is not None:
                restaurants.append(restaurant)
        return restaurants
