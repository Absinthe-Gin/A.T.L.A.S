"""Shared helpers for calling external HTTP services from adapters."""

import logging
import time
from collections import OrderedDict
from collections.abc import Callable, Mapping
from typing import Any

import httpx

from app.core.exceptions import (
    ExternalServiceError,
    ExternalServiceTimeoutError,
    ExternalServiceUnavailableError,
)

logger = logging.getLogger(__name__)


async def get_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    service: str,
    # `httpx.QueryParams` allows a repeated parameter, e.g. several `osm_tag` filters.
    params: Mapping[str, Any] | httpx.QueryParams | None = None,
    headers: Mapping[str, str] | None = None,
    form: Mapping[str, str] | None = None,
    timeout_seconds: float,
) -> Any:
    """GET (or POST `form`) a JSON document; every failure becomes an `ExternalServiceError`.

    `service` names the provider in error codes and logs (e.g. "nominatim").
    The original exception is deliberately not chained (`from None`): its
    message contains the request URL, and the URL may contain an API key.
    """
    started_at = time.perf_counter()
    try:
        if form is None:
            response = await client.get(
                url, params=params, headers=headers, timeout=timeout_seconds
            )
        else:
            response = await client.post(
                url, params=params, data=form, headers=headers, timeout=timeout_seconds
            )
        response.raise_for_status()
        payload = response.json()
    except httpx.TimeoutException as error:
        logger.warning(
            "External service timed out",
            extra={"service": service, "error_type": type(error).__name__},
        )
        raise ExternalServiceTimeoutError(
            "Dịch vụ dữ liệu bên ngoài phản hồi quá lâu.", code=f"{service}_timeout"
        ) from None
    except httpx.HTTPStatusError as error:
        logger.warning(
            "External service returned an error",
            extra={"service": service, "status_code": error.response.status_code},
        )
        raise ExternalServiceError(
            "Dịch vụ dữ liệu bên ngoài trả về lỗi.", code=f"{service}_error"
        ) from None
    except httpx.TransportError as error:
        logger.warning(
            "External service unreachable",
            extra={"service": service, "error_type": type(error).__name__},
        )
        raise ExternalServiceUnavailableError(
            "Không kết nối được tới dịch vụ dữ liệu bên ngoài.", code=f"{service}_unavailable"
        ) from None
    except ValueError:
        logger.warning("External service returned invalid JSON", extra={"service": service})
        raise ExternalServiceError(
            "Dịch vụ dữ liệu bên ngoài trả về dữ liệu không hợp lệ.", code=f"{service}_invalid"
        ) from None
    logger.debug(
        "External service call",
        extra={
            "service": service,
            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
        },
    )
    return payload


class TtlCache[K, V]:
    """Small in-memory cache with expiry, so repeated lookups do not hit free services again."""

    def __init__(
        self,
        *,
        ttl_seconds: float,
        max_entries: int = 256,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_seconds
        self._max = max_entries
        self._clock = clock
        self._entries: OrderedDict[K, tuple[float, V]] = OrderedDict()

    def get(self, key: K) -> V | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if self._clock() >= expires_at:
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return value

    def set(self, key: K, value: V) -> None:
        self._entries[key] = (self._clock() + self._ttl, value)
        self._entries.move_to_end(key)
        while len(self._entries) > self._max:
            self._entries.popitem(last=False)
