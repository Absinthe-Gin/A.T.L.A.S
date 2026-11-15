"""Live travel information from external services: places, weather, ways to get there.

Every answer comes from a named external source. When a source cannot answer,
that part says so; it is never filled with invented data.
"""

import logging
from datetime import date

from app.core.exceptions import ExternalServiceError
from app.infrastructure.external import ExternalServices
from app.infrastructure.flights import ATTRIBUTION as FLIGHT_SOURCE
from app.infrastructure.flights import FlightOffer, google_flights_url
from app.infrastructure.geo import GeoPlace, GeoPoint, distance_km
from app.infrastructure.weather import WeatherForecast
from app.modules.travel.airports import nearest_airport
from app.modules.travel.exceptions import PlaceNotFoundError
from app.modules.travel.schemas import (
    FlightOptions,
    FlightStatus,
    PlaceRef,
    RoadOption,
    TransportLink,
    TransportOptions,
)

logger = logging.getLogger(__name__)

# Below this distance a flight is not a sensible suggestion.
MIN_FLIGHT_DISTANCE_KM = 100.0
MAX_FLIGHT_OFFERS = 10


def _point(place: PlaceRef) -> GeoPoint:
    return GeoPoint(lat=place.lat, lon=place.lon)


def ground_links(origin: PlaceRef, destination: PlaceRef) -> list[TransportLink]:
    """Booking sites for trains and coaches. Atlas has no timetable data from them."""
    route = f"{origin.name} → {destination.name}"
    return [
        TransportLink(
            mode="train",
            provider="Đường sắt Việt Nam (dsvn.vn)",
            url="https://dsvn.vn/",
            hint=f"Chọn ga đi và ga đến cho tuyến {route} để xem giờ tàu và giá vé.",
        ),
        TransportLink(
            mode="bus",
            provider="Vexere",
            url="https://vexere.com/",
            hint=f"Tìm xe khách tuyến {route} để so sánh nhà xe, giờ chạy và giá vé.",
        ),
    ]


class TravelInfoService:
    def __init__(self, external: ExternalServices) -> None:
        self._external = external

    async def search_places(self, query: str, *, limit: int = 5) -> list[GeoPlace]:
        return await self._external.places.search(query, limit=limit)

    async def resolve_place(self, query: str) -> PlaceRef:
        """The best match for a place name, for callers that only have a name (the assistant)."""
        places = await self.search_places(query, limit=1)
        if not places:
            raise PlaceNotFoundError(f"Không tìm thấy địa điểm '{query}'.")
        best = places[0]
        return PlaceRef(name=best.name, lat=best.lat, lon=best.lon)

    async def weather(self, lat: float, lon: float, *, days: int = 7) -> WeatherForecast:
        return await self._external.weather.forecast(lat, lon, days=days)

    async def transport(
        self,
        origin: PlaceRef,
        destination: PlaceRef,
        travel_date: date,
        *,
        adults: int = 1,
        origin_airport: str | None = None,
        destination_airport: str | None = None,
    ) -> TransportOptions:
        """Every way to make the trip, each part answered independently."""
        return TransportOptions(
            origin=origin,
            destination=destination,
            travel_date=travel_date,
            straight_distance_km=round(distance_km(_point(origin), _point(destination)), 1),
            road=await self._road(origin, destination),
            flights=await self._flights(
                origin, destination, travel_date, adults, origin_airport, destination_airport
            ),
            ground_links=ground_links(origin, destination),
        )

    async def _road(self, origin: PlaceRef, destination: PlaceRef) -> RoadOption:
        try:
            route = await self._external.roads.route(_point(origin), _point(destination))
        except ExternalServiceError as error:
            logger.warning("Road routing failed", extra={"error_code": error.code})
            return RoadOption(
                status="unavailable",
                distance_km=None,
                duration_minutes=None,
                message="Chưa tính được quãng đường lúc này. Thử lại sau.",
            )
        if route is None:
            return RoadOption(
                status="no_route",
                distance_km=None,
                duration_minutes=None,
                message="Không có đường bộ nối hai địa điểm.",
            )
        return RoadOption(
            status="ok",
            distance_km=route.distance_km,
            duration_minutes=route.duration_minutes,
            message=None,
        )

    async def _flights(
        self,
        origin: PlaceRef,
        destination: PlaceRef,
        travel_date: date,
        adults: int,
        origin_code: str | None,
        destination_code: str | None,
    ) -> FlightOptions:
        from_airport = origin_code.upper() if origin_code else self._airport_code(origin)
        to_airport = (
            destination_code.upper() if destination_code else self._airport_code(destination)
        )

        def result(
            status: FlightStatus, message: str | None, offers: list[FlightOffer] | None = None
        ) -> FlightOptions:
            url = (
                google_flights_url(from_airport, to_airport, travel_date)
                if from_airport and to_airport
                else None
            )
            return FlightOptions(
                status=status,
                origin_airport=from_airport,
                destination_airport=to_airport,
                offers=offers or [],
                search_url=url,
                message=message,
                source=FLIGHT_SOURCE if status == "ok" else None,
            )

        if from_airport is None or to_airport is None:
            return result(
                "no_airport", "Không có sân bay gần một trong hai địa điểm. Có thể nhập mã sân bay."
            )
        straight = distance_km(_point(origin), _point(destination))
        if from_airport == to_airport or straight < MIN_FLIGHT_DISTANCE_KM:
            return result("too_close", "Hai địa điểm quá gần để đi máy bay.")
        if not self._external.flights.enabled:
            return result(
                "not_configured",
                "Chưa cấu hình SERPAPI_API_KEY nên Atlas chưa lấy được giá vé. "
                "Mở Google Flights để xem.",
            )
        try:
            offers = await self._external.flights.search(
                from_airport, to_airport, travel_date, adults=adults
            )
        except ExternalServiceError as error:
            logger.warning("Flight search failed", extra={"error_code": error.code})
            return result(
                "unavailable", "Chưa tìm được chuyến bay lúc này. Mở Google Flights để xem."
            )
        priced = sorted(offers, key=lambda offer: (offer.price_vnd is None, offer.price_vnd or 0))
        message = None if priced else "Không có chuyến bay nào cho ngày này."
        return result("ok", message, priced[:MAX_FLIGHT_OFFERS])

    @staticmethod
    def _airport_code(place: PlaceRef) -> str | None:
        airport = nearest_airport(_point(place))
        return airport.code if airport else None
