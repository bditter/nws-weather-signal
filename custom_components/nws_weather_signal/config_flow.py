"""Config flow for NWS Weather Signal."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import NwsApiClient, NwsApiError
from .const import (
    CONF_ALERT_LIMIT,
    CONF_AREA,
    CONF_LATITUDE,
    CONF_LOCATION_TYPE,
    CONF_LONGITUDE,
    CONF_ZONE,
    DEFAULT_ALERT_LIMIT,
    DOMAIN,
    LOCATION_AREA,
    LOCATION_POINT,
    LOCATION_ZONE,
    MAX_ALERT_LIMIT,
    MIN_ALERT_LIMIT,
    normalize_alert_limit,
)

_LOCATION_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[LOCATION_POINT, LOCATION_ZONE, LOCATION_AREA],
        mode=SelectSelectorMode.DROPDOWN,
        translation_key="location_type",
    )
)


class NwsWeatherSignalConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._base: dict[str, Any] = {}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Collect a name, location method, and slot count."""
        if user_input is not None:
            self._base = user_input
            return await getattr(
                self,
                f"async_step_{user_input[CONF_LOCATION_TYPE]}",
            )()

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="NWS Weather Signal"): str,
                vol.Required(
                    CONF_LOCATION_TYPE,
                    default=LOCATION_POINT,
                ): _LOCATION_SELECTOR,
                vol.Required(
                    CONF_ALERT_LIMIT,
                    default=DEFAULT_ALERT_LIMIT,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_ALERT_LIMIT,
                        max=MAX_ALERT_LIMIT,
                        step=1,
                        mode="box",
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_point(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Configure a latitude/longitude lookup."""
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_LATITUDE,
                    default=round(self.hass.config.latitude, 4),
                ): vol.All(vol.Coerce(float), vol.Range(min=-90, max=90)),
                vol.Required(
                    CONF_LONGITUDE,
                    default=round(self.hass.config.longitude, 4),
                ): vol.All(vol.Coerce(float), vol.Range(min=-180, max=180)),
            }
        )
        return await self._async_finish_location(
            LOCATION_POINT,
            user_input,
            schema,
        )

    async def async_step_zone(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Configure a forecast-zone or county lookup."""
        schema = vol.Schema({
            vol.Required(CONF_ZONE): vol.All(
                str,
                vol.Upper,
                vol.Match(r"^[A-Z]{2}[ZC]\d{3}$"),
            )
        })
        return await self._async_finish_location(
            LOCATION_ZONE,
            user_input,
            schema,
        )

    async def async_step_area(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Configure a state or marine-area lookup."""
        schema = vol.Schema({
            vol.Required(CONF_AREA): vol.All(
                str,
                vol.Upper,
                vol.Match(r"^[A-Z]{2}$"),
            )
        })
        return await self._async_finish_location(
            LOCATION_AREA,
            user_input,
            schema,
        )

    async def _async_finish_location(
        self,
        location_type: str,
        user_input: dict[str, Any] | None,
        schema: vol.Schema,
    ) -> FlowResult:
        """Validate a location and create the entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = {**self._base, **user_input}
            data[CONF_LOCATION_TYPE] = location_type
            data[CONF_ALERT_LIMIT] = normalize_alert_limit(
                data[CONF_ALERT_LIMIT]
            )
            client = NwsApiClient(
                async_get_clientsession(self.hass),
                data,
                "NWS Weather Signal setup (github.com/bditter/nws-weather-signal)",
            )
            try:
                await client.async_get_active_alerts()
            except NwsApiError:
                errors["base"] = "cannot_connect"
            else:
                title = data.pop(CONF_NAME)
                unique_id = _location_unique_id(data)
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=title, data=data)

        return self.async_show_form(
            step_id=location_type,
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return NwsWeatherSignalOptionsFlow(config_entry)


class NwsWeatherSignalOptionsFlow(config_entries.OptionsFlow):
    """Handle editable options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options."""
        self._config_entry = config_entry
        self._base: dict[str, Any] = {}

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Edit alert slots and choose a location method."""
        if user_input is not None:
            user_input[CONF_ALERT_LIMIT] = normalize_alert_limit(
                user_input[CONF_ALERT_LIMIT]
            )
            self._base = user_input
            return await getattr(
                self,
                f"async_step_{user_input[CONF_LOCATION_TYPE]}",
            )()

        current = self._current_config
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ALERT_LIMIT,
                    default=normalize_alert_limit(
                        current.get(CONF_ALERT_LIMIT, DEFAULT_ALERT_LIMIT)
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_ALERT_LIMIT,
                        max=MAX_ALERT_LIMIT,
                        step=1,
                        mode="box",
                    )
                ),
                vol.Required(
                    CONF_LOCATION_TYPE,
                    default=current.get(CONF_LOCATION_TYPE, LOCATION_POINT),
                ): _LOCATION_SELECTOR,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_point(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Edit a coordinate lookup."""
        current = {**self._config_entry.data, **self._config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_LATITUDE,
                    default=float(
                        current.get(
                            CONF_LATITUDE,
                            round(self.hass.config.latitude, 4),
                        )
                    ),
                ): vol.All(vol.Coerce(float), vol.Range(min=-90, max=90)),
                vol.Required(
                    CONF_LONGITUDE,
                    default=float(
                        current.get(
                            CONF_LONGITUDE,
                            round(self.hass.config.longitude, 4),
                        )
                    ),
                ): vol.All(vol.Coerce(float), vol.Range(min=-180, max=180)),
            }
        )
        return await self._async_finish_location(
            LOCATION_POINT,
            user_input,
            schema,
        )

    async def async_step_zone(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Edit a forecast-zone or county lookup."""
        current = self._current_config
        zone_validator = vol.All(
            str,
            vol.Upper,
            vol.Match(r"^[A-Z]{2}[ZC]\d{3}$"),
        )
        if current.get(CONF_LOCATION_TYPE) == LOCATION_ZONE:
            schema = vol.Schema({
                vol.Required(
                    CONF_ZONE,
                    default=str(current[CONF_ZONE]),
                ): zone_validator
            })
        else:
            schema = vol.Schema({
                vol.Required(CONF_ZONE): zone_validator
            })
        return await self._async_finish_location(
            LOCATION_ZONE,
            user_input,
            schema,
        )

    async def async_step_area(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Edit a state or marine-area lookup."""
        current = self._current_config
        area_validator = vol.All(
            str,
            vol.Upper,
            vol.Match(r"^[A-Z]{2}$"),
        )
        if current.get(CONF_LOCATION_TYPE) == LOCATION_AREA:
            schema = vol.Schema({
                vol.Required(
                    CONF_AREA,
                    default=str(current[CONF_AREA]),
                ): area_validator
            })
        else:
            schema = vol.Schema({
                vol.Required(CONF_AREA): area_validator
            })
        return await self._async_finish_location(
            LOCATION_AREA,
            user_input,
            schema,
        )

    async def _async_finish_location(
        self,
        location_type: str,
        user_input: dict[str, Any] | None,
        schema: vol.Schema,
    ) -> FlowResult:
        """Validate and save edited location options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            options = {
                CONF_ALERT_LIMIT: normalize_alert_limit(
                    self._base.get(
                        CONF_ALERT_LIMIT,
                        self._current_config.get(
                            CONF_ALERT_LIMIT,
                            DEFAULT_ALERT_LIMIT,
                        ),
                    )
                ),
                CONF_LOCATION_TYPE: location_type,
                **user_input,
            }
            try:
                client = NwsApiClient(
                    async_get_clientsession(self.hass),
                    options,
                    "NWS Weather Signal options "
                    "(github.com/bditter/nws-weather-signal)",
                )
                await client.async_get_active_alerts()
            except (KeyError, TypeError, ValueError):
                errors["base"] = "invalid_location"
            except NwsApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(data=options)

        return self.async_show_form(
            step_id=location_type,
            data_schema=schema,
            errors=errors,
        )

    @property
    def _current_config(self) -> dict[str, Any]:
        """Return the effective saved configuration."""
        return {**self._config_entry.data, **self._config_entry.options}


def _location_unique_id(data: dict[str, Any]) -> str:
    """Build a stable location identifier."""
    location_type = data[CONF_LOCATION_TYPE]
    if location_type == LOCATION_POINT:
        return (
            f"point:{float(data[CONF_LATITUDE]):.4f},"
            f"{float(data[CONF_LONGITUDE]):.4f}"
        )
    if location_type == LOCATION_ZONE:
        return f"zone:{str(data[CONF_ZONE]).upper()}"
    return f"area:{str(data[CONF_AREA]).upper()}"
