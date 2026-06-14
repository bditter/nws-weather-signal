"""Tests for weather.gov location URL construction."""

from custom_components.nws_weather_signal.const import (
    CONF_LATITUDE,
    CONF_LOCATION_TYPE,
    CONF_LONGITUDE,
    CONF_ZONE,
    LOCATION_POINT,
    LOCATION_ZONE,
)
from custom_components.nws_weather_signal.location import build_alerts_url


def test_build_point_url_accepts_string_coordinates() -> None:
    """Flow values should be normalized before numeric URL formatting."""
    url = build_alerts_url({
        CONF_LOCATION_TYPE: LOCATION_POINT,
        CONF_LATITUDE: "47.6062",
        CONF_LONGITUDE: "-122.3321",
    })

    assert url.endswith("point=47.6062%2C-122.3321")


def test_build_zone_url_normalizes_case() -> None:
    """Zone codes should be sent to weather.gov in uppercase."""
    url = build_alerts_url({
        CONF_LOCATION_TYPE: LOCATION_ZONE,
        CONF_ZONE: "waz315",
    })

    assert url.endswith("zone=WAZ315")
