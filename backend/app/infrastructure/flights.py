"""Flight offers from Google Flights through SerpApi (needs the user's own key).

https://serpapi.com/google-flights-api
Without a key the adapter is disabled and callers offer a Google Flights link.
"""

from datetime import date
from typing import Any, Protocol
from urllib.parse import quote

import httpx
from pydantic import BaseModel, SecretStr, ValidationError

from app.core.exceptions import ExternalServiceError
from app.infrastructure.http.fetch import TtlCache, get_json

ATTRIBUTION = "Google Flights qua SerpApi"


class FlightSegment(BaseModel):
    airline: str
    flight_number: str | None
    departure_airport: str
    departure_time: str
    arrival_airport: str
    arrival_time: str
    duration_minutes: int | None


class FlightOffer(BaseModel):
    # Whole đồng, as reported by Google Flights for the requested currency.
    price_vnd: int | None
    total_duration_minutes: int | None
    stops: int
    segments: list[FlightSegment]


class FlightSearch(Protocol):
    @property
    def enabled(self) -> bool: ...

    async def search(
        self, origin: str, destination: str, on: date, *, adults: int = 1
    ) -> list[FlightOffer]: ...


def google_flights_url(origin: str, destination: str, on: date) -> str:
    """A Google Flights search the user can open, for when prices cannot be fetched."""
    query = f"Flights from {origin} to {destination} on {on.isoformat()} one way"
    return f"https://www.google.com/travel/flights?q={quote(query)}&hl=vi&curr=VND"


class _Airport(BaseModel):
    id: str
    time: str


class _Segment(BaseModel):
    airline: str
    flight_number: str | None = None
    departure_airport: _Airport
    arrival_airport: _Airport
    duration: int | None = None


class _Offer(BaseModel):
    flights: list[_Segment]
    total_duration: int | None = None
    price: int | None = None


class SerpApiFlights:
    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        api_key: SecretStr,
        timeout_seconds: float,
        cache: TtlCache[tuple[str, str, date, int], list[FlightOffer]] | None = None,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds
        # The free plan has a monthly quota: never repeat the same search within an hour.
        self._cache = cache or TtlCache(ttl_seconds=3600)

    @property
    def enabled(self) -> bool:
        return bool(self._api_key.get_secret_value())

    async def search(
        self, origin: str, destination: str, on: date, *, adults: int = 1
    ) -> list[FlightOffer]:
        key = (origin, destination, on, adults)
        if (cached := self._cache.get(key)) is not None:
            return cached
        payload = await get_json(
            self._client,
            f"{self._base_url}/search.json",
            service="serpapi",
            params={
                "engine": "google_flights",
                "departure_id": origin,
                "arrival_id": destination,
                "outbound_date": on.isoformat(),
                "type": 2,
                "adults": adults,
                "currency": "VND",
                "hl": "vi",
                "gl": "vn",
                "api_key": self._api_key.get_secret_value(),
            },
            timeout_seconds=self._timeout,
        )
        offers = self._parse(payload)
        self._cache.set(key, offers)
        return offers

    @staticmethod
    def _parse(payload: Any) -> list[FlightOffer]:
        if not isinstance(payload, dict):
            raise ExternalServiceError("Dữ liệu chuyến bay không hợp lệ.", code="serpapi_invalid")
        if (
            "error" in payload
            and not payload.get("best_flights")
            and not payload.get("other_flights")
        ):
            # SerpApi reports "no results" as an error message: an empty answer, not a failure.
            message = str(payload["error"]).lower()
            if "no results" in message or "hasn't returned any results" in message:
                return []
            raise ExternalServiceError("Dịch vụ tìm chuyến bay trả về lỗi.", code="serpapi_error")

        offers: list[FlightOffer] = []
        for raw in [*payload.get("best_flights", []), *payload.get("other_flights", [])]:
            try:
                item = _Offer.model_validate(raw)
            except ValidationError:
                continue
            if not item.flights:
                continue
            offers.append(
                FlightOffer(
                    price_vnd=item.price,
                    total_duration_minutes=item.total_duration,
                    stops=len(item.flights) - 1,
                    segments=[
                        FlightSegment(
                            airline=segment.airline,
                            flight_number=segment.flight_number,
                            departure_airport=segment.departure_airport.id,
                            departure_time=segment.departure_airport.time,
                            arrival_airport=segment.arrival_airport.id,
                            arrival_time=segment.arrival_airport.time,
                            duration_minutes=segment.duration,
                        )
                        for segment in item.flights
                    ],
                )
            )
        return offers
