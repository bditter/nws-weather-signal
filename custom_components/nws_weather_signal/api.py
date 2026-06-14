"""Client for the weather.gov alerts API."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession
from yarl import URL

from .const import (
    API_BASE_URL,
    CONF_AREA,
    CONF_LATITUDE,
    CONF_LOCATION_TYPE,
    CONF_LONGITUDE,
    CONF_ZONE,
    LOCATION_AREA,
    LOCATION_POINT,
    LOCATION_ZONE,
)


class NwsApiError(Exception):
    """Base error for weather.gov requests."""


class NwsApiConnectionError(NwsApiError):
    """Raised when weather.gov cannot be reached."""


class NwsApiResponseError(NwsApiError):
    """Raised when weather.gov rejects a request."""


def build_alerts_url(config: dict[str, Any]) -> URL:
    """Build the active-alert URL for a configured location."""
    location_type = config[CONF_LOCATION_TYPE]
    url = URL(f"{API_BASE_URL}/alerts/active")

    if location_type == LOCATION_POINT:
        point = f"{config[CONF_LATITUDE]:.4f},{config[CONF_LONGITUDE]:.4f}"
        return url.with_query(point=point)
    if location_type == LOCATION_ZONE:
        return url.with_query(zone=str(config[CONF_ZONE]).upper())
    if location_type == LOCATION_AREA:
        return url.with_query(area=str(config[CONF_AREA]).upper())
    raise ValueError(f"Unsupported location type: {location_type}")


class NwsApiClient:
    """Small async client for active NWS alerts."""

    def __init__(
        self,
        session: ClientSession,
        config: dict[str, Any],
        user_agent: str,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._url = build_alerts_url(config)
        self._headers = {
            "Accept": "application/geo+json",
            "User-Agent": user_agent,
        }

    async def async_get_active_alerts(self) -> dict[str, Any]:
        """Fetch active alerts."""
        try:
            async with self._session.get(
                self._url,
                headers=self._headers,
                timeout=20,
            ) as response:
                response.raise_for_status()
                return await response.json()
        except ClientResponseError as err:
            raise NwsApiResponseError(
                f"weather.gov returned HTTP {err.status}"
            ) from err
        except (ClientError, TimeoutError) as err:
            raise NwsApiConnectionError("Unable to reach weather.gov") from err
