"""Try data providers in order: when one fails, the next one answers.

Free public services go down, get overloaded or are blocked on some networks.
Only a provider *failure* (`ExternalServiceError`) moves on to the next one; an
empty answer is a real answer and is returned as is.
"""

import logging
from collections.abc import Sequence

from app.core.exceptions import ExternalServiceError
from app.infrastructure.geo import GeoPlace, GeoPoint, PlaceSearch
from app.infrastructure.overpass import Restaurant, RestaurantSearch

logger = logging.getLogger(__name__)


def _provider_name(provider: object) -> str:
    return type(provider).__name__


class FallbackPlaceSearch:
    def __init__(self, providers: Sequence[PlaceSearch]) -> None:
        if not providers:
            raise ValueError("at least one provider is required")
        self._providers = list(providers)

    async def search(self, query: str, *, limit: int = 5) -> list[GeoPlace]:
        last_error: ExternalServiceError | None = None
        for provider in self._providers:
            try:
                return await provider.search(query, limit=limit)
            except ExternalServiceError as error:
                logger.warning(
                    "Place search provider failed; trying the next one",
                    extra={"provider": _provider_name(provider), "error_code": error.code},
                )
                last_error = error
        assert last_error is not None
        raise last_error


class FallbackRestaurantSearch:
    def __init__(self, providers: Sequence[RestaurantSearch]) -> None:
        if not providers:
            raise ValueError("at least one provider is required")
        self._providers = list(providers)

    async def search(
        self, point: GeoPoint, *, name_terms: Sequence[str], radius_m: int, limit: int
    ) -> list[Restaurant]:
        last_error: ExternalServiceError | None = None
        for provider in self._providers:
            try:
                return await provider.search(
                    point, name_terms=name_terms, radius_m=radius_m, limit=limit
                )
            except ExternalServiceError as error:
                logger.warning(
                    "Restaurant search provider failed; trying the next one",
                    extra={"provider": _provider_name(provider), "error_code": error.code},
                )
                last_error = error
        assert last_error is not None
        raise last_error
