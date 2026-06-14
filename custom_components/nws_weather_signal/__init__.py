"""NWS Weather Signal integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import NwsApiClient
from .const import PLATFORMS
from .coordinator import NwsWeatherSignalCoordinator

type NwsWeatherSignalConfigEntry = ConfigEntry[NwsWeatherSignalCoordinator]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NwsWeatherSignalConfigEntry,
) -> bool:
    """Set up NWS Weather Signal from a config entry."""
    config = {**entry.data, **entry.options}
    client = NwsApiClient(
        async_get_clientsession(hass),
        config,
        f"NWS Weather Signal/0.1.0 Home Assistant/{HA_VERSION} "
        "(github.com/bditter/nws-weather-signal)",
    )
    coordinator = NwsWeatherSignalCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: NwsWeatherSignalConfigEntry,
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant,
    entry: NwsWeatherSignalConfigEntry,
) -> None:
    """Reload after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
