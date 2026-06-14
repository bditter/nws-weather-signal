"""Binary sensor platform for NWS Weather Signal."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONF_ALERT_LIMIT,
    DEFAULT_ALERT_LIMIT,
    DOMAIN,
)
from .coordinator import NwsWeatherSignalCoordinator
from .models import NwsAlert


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[NwsWeatherSignalCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up alert-slot sensors."""
    alert_limit = entry.options.get(
        CONF_ALERT_LIMIT,
        entry.data.get(CONF_ALERT_LIMIT, DEFAULT_ALERT_LIMIT),
    )
    async_add_entities(
        NwsAlertSlotBinarySensor(entry, slot)
        for slot in range(alert_limit)
    )


class NwsAlertSlotBinarySensor(
    CoordinatorEntity[NwsWeatherSignalCoordinator],
    BinarySensorEntity,
):
    """A stable slot containing one prioritized active alert."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_icon = "mdi:weather-lightning"

    def __init__(
        self,
        entry: ConfigEntry[NwsWeatherSignalCoordinator],
        slot: int,
    ) -> None:
        """Initialize an alert slot."""
        super().__init__(entry.runtime_data)
        self._slot = slot
        self._attr_unique_id = f"{entry.entry_id}_alert_{slot + 1}"
        self._attr_translation_key = "alert_slot"
        self._attr_translation_placeholders = {"number": str(slot + 1)}
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="U.S. National Weather Service",
            model="Active alerts",
            configuration_url="https://api.weather.gov/alerts",
        )

    @property
    def _alert(self) -> NwsAlert | None:
        """Return the alert occupying this slot."""
        if self._slot >= len(self.coordinator.data):
            return None
        return self.coordinator.data[self._slot]

    @property
    def is_on(self) -> bool:
        """Return whether this slot contains an alert."""
        return self._alert is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return details for this slot's alert."""
        alert = self._alert
        if alert is None:
            return {"slot": self._slot + 1}
        return {"slot": self._slot + 1, **alert.attributes}
