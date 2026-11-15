"""In-memory stand-ins for the external data services. Tests never use the network."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from app.core.exceptions import AppError
from app.infrastructure.external import ExternalServices
from app.infrastructure.flights import FlightOffer, FlightSegment
from app.infrastructure.geo import GeoPlace, GeoPoint, RoadRoute
from app.infrastructure.overpass import Restaurant
from app.infrastructure.weather import CurrentWeather, DailyWeather, WeatherForecast


def place(name: str, lat: float, lon: float) -> GeoPlace:
    return GeoPlace(name=name, display_name=f"{name}, Việt Nam", lat=lat, lon=lon)


HANOI = place("Hà Nội", 21.0285, 105.8542)
HOAN_KIEM = place("Hồ Hoàn Kiếm", 21.0288, 105.8525)
DA_LAT = place("Đà Lạt", 11.9404, 108.4583)
DA_NANG = place("Đà Nẵng", 16.0544, 108.2022)
BAC_NINH = place("Bắc Ninh", 21.1861, 106.0763)

KNOWN_PLACES = {
    "hà nội": [HANOI],
    "hồ hoàn kiếm": [HOAN_KIEM],
    "đà lạt": [DA_LAT],
    "đà nẵng": [DA_NANG],
    "bắc ninh": [BAC_NINH],
}


def flight_offer(price: int | None, stops: int = 0) -> FlightOffer:
    segments = [
        FlightSegment(
            airline="Vietnam Airlines",
            flight_number=f"VN {100 + index}",
            departure_airport="HAN",
            departure_time="2026-12-01 08:00",
            arrival_airport="DLI",
            arrival_time="2026-12-01 10:00",
            duration_minutes=120,
        )
        for index in range(stops + 1)
    ]
    return FlightOffer(price_vnd=price, total_duration_minutes=120, stops=stops, segments=segments)


@dataclass
class FakePlaces:
    places: dict[str, list[GeoPlace]] = field(default_factory=lambda: dict(KNOWN_PLACES))
    error: AppError | None = None
    queries: list[str] = field(default_factory=list)

    async def search(self, query: str, *, limit: int = 5) -> list[GeoPlace]:
        self.queries.append(query)
        if self.error:
            raise self.error
        return self.places.get(query.strip().casefold(), [])[:limit]


@dataclass
class FakeWeather:
    error: AppError | None = None
    requests: list[tuple[float, float, int]] = field(default_factory=list)

    async def forecast(self, lat: float, lon: float, *, days: int = 7) -> WeatherForecast:
        self.requests.append((lat, lon, days))
        if self.error:
            raise self.error
        start = date(2026, 12, 1)
        return WeatherForecast(
            latitude=lat,
            longitude=lon,
            timezone="Asia/Bangkok",
            current=CurrentWeather(
                observed_at=datetime(2026, 12, 1, 9, 0),
                temperature_c=18.5,
                apparent_temperature_c=17.9,
                humidity_percent=82,
                wind_speed_kmh=7.2,
                precipitation_mm=0.0,
                weather_code=2,
                description="Có mây",
            ),
            daily=[
                DailyWeather(
                    date=start + timedelta(days=offset),
                    temperature_max_c=22.0,
                    temperature_min_c=14.0,
                    precipitation_probability_percent=20,
                    weather_code=2,
                    description="Có mây",
                )
                for offset in range(days)
            ],
        )


@dataclass
class FakeRoads:
    route_result: RoadRoute | None = field(
        default_factory=lambda: RoadRoute(distance_km=1480.2, duration_minutes=1500)
    )
    error: AppError | None = None

    async def route(self, origin: GeoPoint, destination: GeoPoint) -> RoadRoute | None:
        if self.error:
            raise self.error
        return self.route_result


@dataclass
class FakeFlights:
    enabled: bool = True
    offers: list[FlightOffer] = field(default_factory=list)
    error: AppError | None = None
    searches: list[tuple[str, str, date, int]] = field(default_factory=list)

    async def search(
        self, origin: str, destination: str, on: date, *, adults: int = 1
    ) -> list[FlightOffer]:
        self.searches.append((origin, destination, on, adults))
        if self.error:
            raise self.error
        return list(self.offers)


@dataclass
class FakeRestaurants:
    restaurants: list[Restaurant] = field(default_factory=list)
    error: AppError | None = None
    searches: list[tuple[tuple[str, ...], float, float, int, int]] = field(default_factory=list)

    async def search(
        self, point: GeoPoint, *, name_terms: Sequence[str], radius_m: int, limit: int
    ) -> list[Restaurant]:
        self.searches.append((tuple(name_terms), point.lat, point.lon, radius_m, limit))
        if self.error:
            raise self.error
        return list(self.restaurants)


@dataclass
class FakeExternal:
    places: FakePlaces = field(default_factory=FakePlaces)
    weather: FakeWeather = field(default_factory=FakeWeather)
    roads: FakeRoads = field(default_factory=FakeRoads)
    flights: FakeFlights = field(default_factory=FakeFlights)
    restaurants: FakeRestaurants = field(default_factory=FakeRestaurants)

    @property
    def services(self) -> ExternalServices:
        return ExternalServices(
            places=self.places,
            weather=self.weather,
            roads=self.roads,
            flights=self.flights,
            restaurants=self.restaurants,
        )
