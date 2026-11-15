"""Place and restaurant search through Photon (OpenStreetMap data, free, no key).

https://photon.komoot.io

Photon answers from the same OpenStreetMap data as Nominatim and Overpass but
from a different host, so it still works where `openstreetmap.org` is blocked.
"""

import math
import unicodedata
from collections.abc import Sequence
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.core.exceptions import ExternalServiceError
from app.infrastructure.geo import GeoPlace, GeoPoint, distance_km
from app.infrastructure.http.fetch import TtlCache, get_json
from app.infrastructure.overpass import MAX_LIMIT, MAX_RADIUS_M, Restaurant

# Query parameters as pairs, so a name such as `osm_tag` can repeat.
_Params = list[tuple[str, str | int | float | bool | None]]

_OSM_TYPES = {"N": "node", "W": "way", "R": "relation"}
_RESTAURANT_TAGS = ("amenity:restaurant", "amenity:fast_food", "amenity:cafe")
# Photon ranks by text first; ask for more than needed, then keep those in the radius.
_CANDIDATES_PER_TERM = 50


def fold(text: str) -> str:
    """Lower-case text without diacritics, so "pho" matches "Phở" and "do" matches "đỗ"."""
    decomposed = unicodedata.normalize("NFD", text.casefold().replace("đ", "d"))
    return "".join(char for char in decomposed if not unicodedata.combining(char))


class _Properties(BaseModel):
    name: str | None = None
    osm_type: str | None = None
    osm_id: int | None = None
    osm_key: str | None = None
    osm_value: str | None = None
    housenumber: str | None = None
    street: str | None = None
    district: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None


class _Geometry(BaseModel):
    coordinates: tuple[float, float]


class _Feature(BaseModel):
    properties: _Properties
    geometry: _Geometry


def _features(payload: Any) -> list[_Feature]:
    if not isinstance(payload, dict) or not isinstance(payload.get("features"), list):
        raise ExternalServiceError("Dữ liệu địa điểm không hợp lệ.", code="photon_invalid")
    features: list[_Feature] = []
    for raw in payload["features"]:
        try:
            features.append(_Feature.model_validate(raw))
        except ValidationError:
            # One malformed feature must not hide the others.
            continue
    return features


def _join(*parts: str | None) -> str | None:
    text = ", ".join(part for part in parts if part)
    return text or None


class _PhotonClient:
    def __init__(
        self, client: httpx.AsyncClient, *, base_url: str, user_agent: str, timeout_seconds: float
    ) -> None:
        self._client = client
        self._url = f"{base_url.rstrip('/')}/api/"
        self._headers = {"User-Agent": user_agent}
        self._timeout = timeout_seconds

    async def _search(self, params: _Params) -> list[_Feature]:
        payload = await get_json(
            self._client,
            self._url,
            service="photon",
            params=httpx.QueryParams(params),
            headers=self._headers,
            timeout_seconds=self._timeout,
        )
        return _features(payload)


class PhotonGeocoder(_PhotonClient):
    """Place search. `bias` ranks places near that point first (Atlas biases to Vietnam)."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        user_agent: str,
        timeout_seconds: float,
        bias: GeoPoint | None = None,
        cache: TtlCache[tuple[str, int], list[GeoPlace]] | None = None,
    ) -> None:
        super().__init__(
            client, base_url=base_url, user_agent=user_agent, timeout_seconds=timeout_seconds
        )
        self._bias = bias
        self._cache = cache or TtlCache(ttl_seconds=24 * 3600)

    async def search(self, query: str, *, limit: int = 5) -> list[GeoPlace]:
        key = (query.strip().casefold(), limit)
        if (cached := self._cache.get(key)) is not None:
            return cached
        params: _Params = [("q", query.strip()), ("limit", limit)]
        if self._bias is not None:
            params += [("lat", self._bias.lat), ("lon", self._bias.lon)]
        places = [self._place(feature) for feature in await self._search(params)]
        found = [place for place in places if place is not None]
        self._cache.set(key, found)
        return found

    @staticmethod
    def _place(feature: _Feature) -> GeoPlace | None:
        props = feature.properties
        if not props.name:
            return None
        lon, lat = feature.geometry.coordinates
        return GeoPlace(
            name=props.name,
            display_name=_join(
                props.name, props.street, props.district, props.city, props.state, props.country
            )
            or props.name,
            lat=lat,
            lon=lon,
            category=props.osm_key,
            type=props.osm_value,
            osm_type=_OSM_TYPES.get(props.osm_type or ""),
            osm_id=props.osm_id,
        )


class PhotonRestaurants(_PhotonClient):
    """Restaurants whose name contains a term, within a radius of a point, nearest first."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        user_agent: str,
        timeout_seconds: float,
        cache: TtlCache[tuple[tuple[str, ...], float, float, int, int], list[Restaurant]]
        | None = None,
    ) -> None:
        super().__init__(
            client, base_url=base_url, user_agent=user_agent, timeout_seconds=timeout_seconds
        )
        self._cache = cache or TtlCache(ttl_seconds=3600)

    async def search(
        self, point: GeoPoint, *, name_terms: Sequence[str], radius_m: int, limit: int
    ) -> list[Restaurant]:
        radius_m = min(max(radius_m, 100), MAX_RADIUS_M)
        limit = min(max(limit, 1), MAX_LIMIT)
        terms = tuple(dict.fromkeys(term.strip().lower() for term in name_terms if term.strip()))
        key = (terms, round(point.lat, 3), round(point.lon, 3), radius_m, limit)
        if (cached := self._cache.get(key)) is not None:
            return cached

        wanted = [fold(term) for term in terms]
        found: dict[tuple[str, int], tuple[float, Restaurant]] = {}
        for term in terms:
            params: _Params = [
                ("q", term),
                ("lat", point.lat),
                ("lon", point.lon),
                ("limit", _CANDIDATES_PER_TERM),
            ]
            params += [("osm_tag", tag) for tag in _RESTAURANT_TAGS]
            for feature in await self._search(params):
                restaurant = self._restaurant(feature)
                if restaurant is None or not any(word in fold(restaurant.name) for word in wanted):
                    continue
                distance = distance_km(point, GeoPoint(lat=restaurant.lat, lon=restaurant.lon))
                if distance * 1000 <= radius_m:
                    found[(restaurant.osm_type, restaurant.osm_id)] = (distance, restaurant)

        nearest = [restaurant for _, restaurant in sorted(found.values(), key=lambda pair: pair[0])]
        result = nearest[:limit]
        self._cache.set(key, result)
        return result

    @staticmethod
    def _restaurant(feature: _Feature) -> Restaurant | None:
        props = feature.properties
        osm_type = _OSM_TYPES.get(props.osm_type or "")
        if not props.name or osm_type is None or props.osm_id is None:
            return None
        lon, lat = feature.geometry.coordinates
        if not (math.isfinite(lat) and math.isfinite(lon)):
            return None
        return Restaurant(
            osm_type=osm_type,
            osm_id=props.osm_id,
            name=props.name,
            lat=lat,
            lon=lon,
            cuisine=None,
            address=_join(props.housenumber, props.street, props.city),
            # Photon does not carry opening hours, phone or website: left empty, never guessed.
        )
