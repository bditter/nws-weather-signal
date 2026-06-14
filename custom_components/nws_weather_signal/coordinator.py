"""Update coordinator for NWS Weather Signal."""

from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .api import NwsApiClient, NwsApiError
from .const import (
    CONF_ALERT_LIMIT,
    DEFAULT_ALERT_LIMIT,
    DOMAIN,
    UPDATE_INTERVAL,
    normalize_alert_limit,
)
from .models import NwsAlert, parse_alerts

LOGGER = logging.getLogger(__name__)


class NwsWeatherSignalCoordinator(DataUpdateCoordinator[tuple[NwsAlert, ...]]):
    """Fetch and distribute active NWS alerts."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: NwsApiClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            always_update=False,
        )
        self._client = client
        self.last_successful_update: datetime | None = None
        self._alert_limit = normalize_alert_limit(
            entry.options.get(
                CONF_ALERT_LIMIT,
                entry.data.get(CONF_ALERT_LIMIT, DEFAULT_ALERT_LIMIT),
            )
        )

    async def _async_update_data(self) -> tuple[NwsAlert, ...]:
        """Fetch and normalize active alerts."""
        try:
            payload = await self._client.async_get_active_alerts()
        except NwsApiError as err:
            raise UpdateFailed(str(err)) from err
        alerts = parse_alerts(payload, self._alert_limit)
        self.last_successful_update = dt_util.utcnow()
        return alerts

    @property
    def request_url(self) -> str:
        """Return the weather.gov request URL."""
        return self._client.url
