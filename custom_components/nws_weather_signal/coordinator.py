"""Update coordinator for NWS Weather Signal."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import NwsApiClient, NwsApiError
from .const import CONF_ALERT_LIMIT, DEFAULT_ALERT_LIMIT, DOMAIN, UPDATE_INTERVAL
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
        self._alert_limit = entry.options.get(
            CONF_ALERT_LIMIT,
            entry.data.get(CONF_ALERT_LIMIT, DEFAULT_ALERT_LIMIT),
        )

    async def _async_update_data(self) -> tuple[NwsAlert, ...]:
        """Fetch and normalize active alerts."""
        try:
            payload = await self._client.async_get_active_alerts()
        except NwsApiError as err:
            raise UpdateFailed(str(err)) from err
        return parse_alerts(payload, self._alert_limit)
