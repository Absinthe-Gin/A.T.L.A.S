import uuid
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.infrastructure.flights import FlightOffer


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("Không được để trống.")
    return stripped


class PlaceRef(BaseModel):
    """A named point, as chosen from place search."""

    name: str = Field(min_length=1, max_length=200)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

    _name = field_validator("name")(_required)


# --- Plans -------------------------------------------------------------------


class PlanCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    destination: PlaceRef | None = None
    start_date: date | None = None
    end_date: date | None = None
    note: str | None = Field(default=None, max_length=2000)

    _title = field_validator("title")(_required)
    _note = field_validator("note")(_clean)


class PlanUpdate(BaseModel):
    """Omitted fields keep their value; `destination: null` removes it."""

    title: str | None = Field(default=None, min_length=1, max_length=120)
    destination: PlaceRef | None = None
    start_date: date | None = None
    end_date: date | None = None
    note: str | None = Field(default=None, max_length=2000)

    _note = field_validator("note")(_clean)


class PlanOut(BaseModel):
    id: uuid.UUID
    title: str
    destination: PlaceRef | None
    start_date: date | None
    end_date: date | None
    note: str | None
    item_count: int
    created_at: datetime


# --- Itinerary ---------------------------------------------------------------


class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    day: date | None = None
    start_time: time | None = None
    place: PlaceRef | None = None
    note: str | None = Field(default=None, max_length=2000)

    _title = field_validator("title")(_required)
    _note = field_validator("note")(_clean)


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    day: date | None = None
    start_time: time | None = None
    place: PlaceRef | None = None
    note: str | None = Field(default=None, max_length=2000)

    _note = field_validator("note")(_clean)


class ItemOut(BaseModel):
    id: uuid.UUID
    title: str
    day: date | None
    start_time: time | None
    place: PlaceRef | None
    note: str | None


class PlanDetail(PlanOut):
    items: list[ItemOut]


# --- Live information --------------------------------------------------------


class TransportLink(BaseModel):
    """A booking site the user opens themselves; Atlas has no data from it."""

    mode: Literal["flight", "train", "bus"]
    provider: str
    url: str
    hint: str


# ok: prices found; not_configured: no SerpApi key; no_airport: no airport near one
# end; too_close: flying makes no sense; unavailable: the provider failed.
FlightStatus = Literal["ok", "not_configured", "no_airport", "too_close", "unavailable"]


class FlightOptions(BaseModel):
    status: FlightStatus
    origin_airport: str | None
    destination_airport: str | None
    offers: list[FlightOffer]
    search_url: str | None
    message: str | None
    source: str | None


class RoadOption(BaseModel):
    status: Literal["ok", "no_route", "unavailable"]
    distance_km: float | None
    duration_minutes: int | None
    message: str | None


class TransportOptions(BaseModel):
    origin: PlaceRef
    destination: PlaceRef
    travel_date: date
    straight_distance_km: float
    road: RoadOption
    flights: FlightOptions
    ground_links: list[TransportLink]
