"""Constants for NWS Weather Signal."""

from datetime import timedelta
from typing import Any

DOMAIN = "nws_weather_signal"
PLATFORMS = ["binary_sensor", "sensor"]
VERSION = "1.0.2"

CONF_AREA = "area"
CONF_ALERT_LIMIT = "alert_limit"
CONF_LATITUDE = "latitude"
CONF_LOCATION_TYPE = "location_type"
CONF_LONGITUDE = "longitude"
CONF_ZONE = "zone"

LOCATION_AREA = "area"
LOCATION_POINT = "point"
LOCATION_ZONE = "zone"

DEFAULT_ALERT_LIMIT = 2
MAX_ALERT_LIMIT = 10
MIN_ALERT_LIMIT = 1
UPDATE_INTERVAL = timedelta(minutes=1)

API_BASE_URL = "https://api.weather.gov"
ATTRIBUTION = "Data provided by the U.S. National Weather Service"


def normalize_alert_limit(value: Any) -> int:
    """Return a valid integer alert-slot count."""
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return DEFAULT_ALERT_LIMIT
    return max(MIN_ALERT_LIMIT, min(limit, MAX_ALERT_LIMIT))
