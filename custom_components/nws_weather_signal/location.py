"""Location query construction for NWS Weather Signal."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

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


def build_alerts_url(config: dict[str, Any]) -> str:
    """Build the active-alert URL for a configured location."""
    location_type = config[CONF_LOCATION_TYPE]

    if location_type == LOCATION_POINT:
        latitude = float(config[CONF_LATITUDE])
        longitude = float(config[CONF_LONGITUDE])
        query = {"point": f"{latitude:.4f},{longitude:.4f}"}
    elif location_type == LOCATION_ZONE:
        query = {"zone": str(config[CONF_ZONE]).upper()}
    elif location_type == LOCATION_AREA:
        query = {"area": str(config[CONF_AREA]).upper()}
    else:
        raise ValueError(f"Unsupported location type: {location_type}")

    return f"{API_BASE_URL}/alerts/active?{urlencode(query)}"
