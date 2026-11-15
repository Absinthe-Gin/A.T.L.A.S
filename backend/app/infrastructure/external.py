"""All adapters to external data services, built once at startup."""

from dataclasses import dataclass

import httpx

from app import __version__
from app.core.config import Settings
from app.infrastructure.fallback import FallbackPlaceSearch, FallbackRestaurantSearch
from app.infrastructure.flights import FlightSearch, SerpApiFlights
from app.infrastructure.geo import GeoPoint, NominatimGeocoder, OsrmRouter, PlaceSearch, RoadRouter
from app.infrastructure.overpass import OverpassRestaurants, RestaurantSearch
from app.infrastructure.photon import PhotonGeocoder, PhotonRestaurants
from app.infrastructure.weather import OpenMeteoWeather, WeatherService

# Atlas is built for Vietnam: place names are ranked nearer this point first
# (Photon otherwise prefers famous matches anywhere, e.g. "Huế" in Hungary).
VIETNAM_CENTER = GeoPoint(lat=16.0, lon=106.5)


@dataclass(frozen=True)
class ExternalServices:
    places: PlaceSearch
    weather: WeatherService
    roads: RoadRouter
    flights: FlightSearch
    restaurants: RestaurantSearch


def user_agent(settings: Settings) -> str:
    """Identifies this application to OpenStreetMap services, as their policy asks."""
    contact = f"; {settings.osm_contact}" if settings.osm_contact else ""
    return f"ATLAS-Personal-Assistant/{__version__} (self-hosted{contact})"


def build_external_services(settings: Settings, client: httpx.AsyncClient) -> ExternalServices:
    """Create the adapters. Nothing is contacted until a request needs it.

    Place and restaurant search each have a second provider on another host, so
    one blocked, overloaded or unreachable service does not stop the feature.
    """
    agent = user_agent(settings)
    timeout = settings.external_timeout_seconds
    return ExternalServices(
        places=FallbackPlaceSearch(
            [
                NominatimGeocoder(
                    client,
                    base_url=settings.nominatim_base_url,
                    user_agent=agent,
                    timeout_seconds=timeout,
                ),
                PhotonGeocoder(
                    client,
                    base_url=settings.photon_base_url,
                    user_agent=agent,
                    timeout_seconds=timeout,
                    bias=VIETNAM_CENTER,
                ),
            ]
        ),
        weather=OpenMeteoWeather(
            client, base_url=settings.open_meteo_base_url, timeout_seconds=timeout
        ),
        roads=OsrmRouter(
            client, base_url=settings.osrm_base_url, user_agent=agent, timeout_seconds=timeout
        ),
        flights=SerpApiFlights(
            client,
            base_url=settings.serpapi_base_url,
            api_key=settings.serpapi_api_key,
            timeout_seconds=timeout,
        ),
        # Photon answers in about a second; the public Overpass server is often
        # overloaded and slow, so it is only the fallback.
        restaurants=FallbackRestaurantSearch(
            [
                PhotonRestaurants(
                    client,
                    base_url=settings.photon_base_url,
                    user_agent=agent,
                    timeout_seconds=timeout,
                ),
                OverpassRestaurants(
                    client,
                    base_url=settings.overpass_base_url,
                    timeout_seconds=settings.overpass_timeout_seconds,
                    user_agent=agent,
                ),
            ]
        ),
    )
