"""Place search (OpenStreetMap Nominatim) and road routing (OSRM).

Both are free public services with usage policies: Nominatim allows at most
one request per second and asks for an identifying User-Agent; results are
cached so the same search is not repeated.
"""

import asyncio
import math
import time
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, ValidationError

from app.core.exceptions import ExternalServiceError
from app.infrastructure.http.fetch import TtlCache, get_json

ATTRIBUTION = "© OpenStreetMap contributors"


class GeoPoint(BaseModel):
    lat: float
    lon: float


class GeoPlace(BaseModel):
    """A place found on OpenStreetMap. Optional fields may be missing in the source."""

    name: str
    display_name: str
    lat: float
    lon: float
    category: str | None = None
    type: str | None = None
    osm_type: str | None = None
    osm_id: int | None = None


class RoadRoute(BaseModel):
    distance_km: float
    duration_minutes: int


class PlaceSearch(Protocol):
    async def search(self, query: str, *, limit: int = 5) -> list[GeoPlace]: ...


class RoadRouter(Protocol):
    async def route(self, origin: GeoPoint, destination: GeoPoint) -> RoadRoute | None: ...


def distance_km(a: GeoPoint, b: GeoPoint) -> float:
    """Great-circle distance (haversine)."""
    radius = 6371.0
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat = lat2 - lat1
    dlon = math.radians(b.lon - a.lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


class _NominatimItem(BaseModel):
    lat: str
    lon: str
    display_name: str
    name: str | None = None
    category: str | None = None
    type: str | None = None
    osm_type: str | None = None
    osm_id: int | None = None


class NominatimGeocoder:
    """Adapter for https://nominatim.org/release-docs/latest/api/Search/ ."""

    MIN_INTERVAL_SECONDS = 1.0

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        user_agent: str,
        timeout_seconds: float,
        cache: TtlCache[tuple[str, int], list[GeoPlace]] | None = None,
        min_interval_seconds: float = MIN_INTERVAL_SECONDS,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._headers = {"User-Agent": user_agent, "Accept-Language": "vi,en"}
        self._timeout = timeout_seconds
        self._cache = cache or TtlCache(ttl_seconds=24 * 3600)
        self._min_interval = min_interval_seconds
        self._lock = asyncio.Lock()
        self._last_request = 0.0

    async def search(self, query: str, *, limit: int = 5) -> list[GeoPlace]:
        key = (query.strip().casefold(), limit)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        async with self._lock:
            # Nominatim policy: no more than one request per second from one application.
            wait = self._min_interval - (time.monotonic() - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                payload = await get_json(
                    self._client,
                    f"{self._base_url}/search",
                    service="nominatim",
                    params={"q": query, "format": "jsonv2", "limit": limit, "addressdetails": 0},
                    headers=self._headers,
                    timeout_seconds=self._timeout,
                )
            finally:
                self._last_request = time.monotonic()

        places = self._parse(payload)
        self._cache.set(key, places)
        return places

    @staticmethod
    def _parse(payload: Any) -> list[GeoPlace]:
        if not isinstance(payload, list):
            raise ExternalServiceError("Dữ liệu địa điểm không hợp lệ.", code="nominatim_invalid")
        places = []
        for raw in payload:
            try:
                item = _NominatimItem.model_validate(raw)
                lat, lon = float(item.lat), float(item.lon)
            except (ValidationError, ValueError):
                # One malformed entry must not hide the others.
                continue
            places.append(
                GeoPlace(
                    name=item.name or item.display_name.split(",")[0].strip(),
                    display_name=item.display_name,
                    lat=lat,
                    lon=lon,
                    category=item.category,
                    type=item.type,
                    osm_type=item.osm_type,
                    osm_id=item.osm_id,
                )
            )
        return places


class OsrmRouter:
    """Adapter for the OSRM route service (driving profile)."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        user_agent: str,
        timeout_seconds: float,
        cache: TtlCache[tuple[float, float, float, float], RoadRoute | None] | None = None,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._headers = {"User-Agent": user_agent}
        self._timeout = timeout_seconds
        self._cache = cache or TtlCache(ttl_seconds=6 * 3600)

    async def route(self, origin: GeoPoint, destination: GeoPoint) -> RoadRoute | None:
        """Driving distance and time, or None when no road connects the two points."""
        key = (
            round(origin.lat, 4),
            round(origin.lon, 4),
            round(destination.lat, 4),
            round(destination.lon, 4),
        )
        if (cached := self._cache.get(key)) is not None:
            return cached

        coordinates = f"{origin.lon},{origin.lat};{destination.lon},{destination.lat}"
        payload = await get_json(
            self._client,
            f"{self._base_url}/route/v1/driving/{coordinates}",
            service="osrm",
            params={"overview": "false"},
            headers=self._headers,
            timeout_seconds=self._timeout,
        )
        if not isinstance(payload, dict):
            raise ExternalServiceError("Dữ liệu tuyến đường không hợp lệ.", code="osrm_invalid")
        if payload.get("code") != "Ok" or not payload.get("routes"):
            return None
        try:
            best = payload["routes"][0]
            route = RoadRoute(
                distance_km=round(float(best["distance"]) / 1000, 1),
                duration_minutes=round(float(best["duration"]) / 60),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ExternalServiceError(
                "Dữ liệu tuyến đường không hợp lệ.", code="osrm_invalid"
            ) from error
        self._cache.set(key, route)
        return route
