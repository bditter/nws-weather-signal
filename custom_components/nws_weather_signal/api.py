"""Client for the weather.gov alerts API."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .location import build_alerts_url


class NwsApiError(Exception):
    """Base error for weather.gov requests."""


class NwsApiConnectionError(NwsApiError):
    """Raised when weather.gov cannot be reached."""


class NwsApiResponseError(NwsApiError):
    """Raised when weather.gov rejects a request."""

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

    @property
    def url(self) -> str:
        """Return the configured alerts request URL."""
        return str(self._url)

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
