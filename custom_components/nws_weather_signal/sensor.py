"""Sensor platform for NWS Weather Signal."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import NwsWeatherSignalCoordinator
from .models import active_alert_list_attributes


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[NwsWeatherSignalCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up aggregate alert sensors."""
    async_add_entities([NwsActiveWeatherAlertsListSensor(entry)])


class NwsActiveWeatherAlertsListSensor(
    CoordinatorEntity[NwsWeatherSignalCoordinator],
    SensorEntity,
):
    """A count sensor with aggregate details for all active alerts."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_icon = "mdi:format-list-bulleted"
    _attr_translation_key = "active_weather_alerts_list"

    def __init__(
        self,
        entry: ConfigEntry[NwsWeatherSignalCoordinator],
    ) -> None:
        """Initialize the active-alert list sensor."""
        super().__init__(entry.runtime_data)
        self._attr_unique_id = f"{entry.entry_id}_active_weather_alerts_list"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="U.S. National Weather Service",
            model="Active alerts",
            configuration_url="https://api.weather.gov/alerts",
        )

    @property
    def native_value(self) -> int:
        """Return the number of active alerts."""
        return len(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return aggregate active-alert details."""
        return {
            "configured_location": self.coordinator.request_url,
            "active_alert_count": len(self.coordinator.data),
            "last_successful_update": self.coordinator.last_successful_update,
            "update_interval_minutes": 1,
            **active_alert_list_attributes(self.coordinator.data),
        }
