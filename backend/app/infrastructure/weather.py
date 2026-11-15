"""Current weather and daily forecast from Open-Meteo (free, no key).

https://open-meteo.com/en/docs
"""

from datetime import date, datetime
from typing import Any, Protocol

import httpx
from pydantic import BaseModel, ValidationError

from app.core.exceptions import ExternalServiceError
from app.infrastructure.http.fetch import TtlCache, get_json

ATTRIBUTION = "Weather data by Open-Meteo.com"

# WMO weather interpretation codes, as listed in the Open-Meteo documentation.
_WMO_DESCRIPTIONS: dict[int, str] = {
    0: "Trời quang",
    1: "Ít mây",
    2: "Có mây",
    3: "Nhiều mây",
    45: "Sương mù",
    48: "Sương mù đóng băng",
    51: "Mưa phùn nhẹ",
    53: "Mưa phùn",
    55: "Mưa phùn dày",
    56: "Mưa phùn lạnh",
    57: "Mưa phùn lạnh dày",
    61: "Mưa nhỏ",
    63: "Mưa vừa",
    65: "Mưa to",
    66: "Mưa lạnh",
    67: "Mưa lạnh to",
    71: "Tuyết nhẹ",
    73: "Tuyết",
    75: "Tuyết dày",
    77: "Hạt tuyết",
    80: "Mưa rào nhẹ",
    81: "Mưa rào",
    82: "Mưa rào rất to",
    85: "Mưa tuyết nhẹ",
    86: "Mưa tuyết",
    95: "Dông",
    96: "Dông kèm mưa đá",
    99: "Dông kèm mưa đá lớn",
}


def describe_weather(code: int) -> str:
    return _WMO_DESCRIPTIONS.get(code, "Không rõ")


class CurrentWeather(BaseModel):
    observed_at: datetime
    temperature_c: float
    apparent_temperature_c: float
    humidity_percent: int
    wind_speed_kmh: float
    precipitation_mm: float
    weather_code: int
    description: str


class DailyWeather(BaseModel):
    date: date
    temperature_max_c: float
    temperature_min_c: float
    precipitation_probability_percent: int | None
    weather_code: int
    description: str


class WeatherForecast(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    current: CurrentWeather
    daily: list[DailyWeather]
    source: str = ATTRIBUTION


class WeatherService(Protocol):
    async def forecast(self, lat: float, lon: float, *, days: int = 7) -> WeatherForecast: ...


class OpenMeteoWeather:
    CURRENT = (
        "temperature_2m,relative_humidity_2m,apparent_temperature,"
        "precipitation,weather_code,wind_speed_10m"
    )
    DAILY = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        timeout_seconds: float,
        cache: TtlCache[tuple[float, float, int], WeatherForecast] | None = None,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        # Open-Meteo updates current conditions every 15 minutes.
        self._cache = cache or TtlCache(ttl_seconds=10 * 60)

    async def forecast(self, lat: float, lon: float, *, days: int = 7) -> WeatherForecast:
        key = (round(lat, 3), round(lon, 3), days)
        if (cached := self._cache.get(key)) is not None:
            return cached
        payload = await get_json(
            self._client,
            f"{self._base_url}/v1/forecast",
            service="open_meteo",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": self.CURRENT,
                "daily": self.DAILY,
                "timezone": "auto",
                "forecast_days": days,
                "wind_speed_unit": "kmh",
            },
            timeout_seconds=self._timeout,
        )
        forecast = self._parse(payload)
        self._cache.set(key, forecast)
        return forecast

    @staticmethod
    def _parse(payload: Any) -> WeatherForecast:
        try:
            current = payload["current"]
            daily = payload["daily"]
            probabilities = daily.get("precipitation_probability_max") or [None] * len(
                daily["time"]
            )
            return WeatherForecast(
                latitude=payload["latitude"],
                longitude=payload["longitude"],
                timezone=payload.get("timezone", "UTC"),
                current=CurrentWeather(
                    observed_at=current["time"],
                    temperature_c=current["temperature_2m"],
                    apparent_temperature_c=current["apparent_temperature"],
                    humidity_percent=round(current["relative_humidity_2m"]),
                    wind_speed_kmh=current["wind_speed_10m"],
                    precipitation_mm=current["precipitation"],
                    weather_code=current["weather_code"],
                    description=describe_weather(current["weather_code"]),
                ),
                daily=[
                    DailyWeather(
                        date=day,
                        temperature_max_c=daily["temperature_2m_max"][index],
                        temperature_min_c=daily["temperature_2m_min"][index],
                        precipitation_probability_percent=probabilities[index],
                        weather_code=daily["weather_code"][index],
                        description=describe_weather(daily["weather_code"][index]),
                    )
                    for index, day in enumerate(daily["time"])
                ],
            )
        except (KeyError, IndexError, TypeError, ValidationError) as error:
            raise ExternalServiceError(
                "Dữ liệu thời tiết không hợp lệ.", code="open_meteo_invalid"
            ) from error
