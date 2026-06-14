"""Tests for NWS alert normalization."""

from custom_components.nws_weather_signal.models import (
    active_alert_list_attributes,
    empty_alert_attributes,
    parse_alerts,
)


def _feature(
    alert_id: str,
    severity: str,
    urgency: str = "Expected",
    sent: str = "2026-06-14T10:00:00-04:00",
) -> dict:
    return {
        "id": f"https://api.weather.gov/alerts/{alert_id}",
        "properties": {
            "id": alert_id,
            "@id": f"https://api.weather.gov/alerts/{alert_id}",
            "event": "Test Warning",
            "headline": f"Test Warning {alert_id}",
            "description": "Take cover.",
            "instruction": "Move indoors.",
            "severity": severity,
            "urgency": urgency,
            "certainty": "Likely",
            "status": "Actual",
            "messageType": "Alert",
            "areaDesc": "Test County",
            "sent": sent,
            "eventCode": {
                "NationalWeatherService": ["TOR"],
                "SAME": ["TOR"],
            },
            "affectedZones": ["https://api.weather.gov/zones/county/XXC001"],
        },
    }


def test_parse_alerts_prioritizes_and_limits() -> None:
    """The most severe alert should occupy the first slot."""
    payload = {
        "features": [
            _feature("minor", "Minor"),
            _feature("extreme", "Extreme"),
            _feature("severe", "Severe"),
        ]
    }

    alerts = parse_alerts(payload, 2)

    assert [alert.alert_id for alert in alerts] == ["extreme", "severe"]


def test_parse_alerts_exposes_cap_fields() -> None:
    """CAP event codes and text should become direct attributes."""
    alert = parse_alerts({"features": [_feature("one", "Severe")]}, 1)[0]

    assert alert.attributes["title"] == "Test Warning one"
    assert alert.attributes["nws_code"] == "TOR"
    assert alert.attributes["same_code"] == "TOR"
    assert alert.attributes["affected_zones"] == (
        "https://api.weather.gov/zones/county/XXC001"
    )
    assert alert.attributes["description"] == "Take cover."
    assert alert.attributes["instruction"] == "Move indoors."


def test_parse_alerts_deduplicates_ids() -> None:
    """Duplicate alert IDs should not consume multiple slots."""
    payload = {"features": [_feature("same", "Minor"), _feature("same", "Severe")]}

    alerts = parse_alerts(payload, 10)

    assert len(alerts) == 1
    assert alerts[0].severity == "Severe"


def test_parse_alerts_handles_empty_response() -> None:
    """No API features should produce no active slots."""
    assert parse_alerts({"features": []}, 2) == ()


def test_parse_alerts_accepts_number_selector_float() -> None:
    """Home Assistant number-selector values should be safe slice bounds."""
    payload = {
        "features": [
            _feature("one", "Extreme"),
            _feature("two", "Severe"),
            _feature("three", "Moderate"),
        ]
    }

    alerts = parse_alerts(payload, 2.0)

    assert [alert.alert_id for alert in alerts] == ["one", "two"]


def test_empty_alert_attributes_match_active_schema() -> None:
    """Inactive slots should retain every automation-facing attribute."""
    active = parse_alerts({"features": [_feature("one", "Severe")]}, 1)[0]
    empty = empty_alert_attributes()

    assert empty.keys() == active.attributes.keys()
    assert empty["title"] == "None"
    assert empty["nws_code"] == "None"
    assert empty["same_code"] == "None"
    assert empty["affected_zones"] == "None"
    assert empty["severity"] == "None"
    assert all(value == "None" for value in empty.values())
    assert not any(isinstance(value, list) for value in empty.values())


def test_active_alert_attributes_never_expose_lists() -> None:
    """Every Home Assistant alert attribute should be a scalar value."""
    alert = parse_alerts({"features": [_feature("one", "Severe")]}, 1)[0]

    assert not any(
        isinstance(value, list) for value in alert.attributes.values()
    )


def test_missing_active_values_use_visible_none_string() -> None:
    """Missing CAP fields should not become blank or unavailable values."""
    feature = _feature("one", "Severe")
    feature["properties"].pop("eventCode")
    feature["properties"].pop("affectedZones")
    feature["properties"].pop("instruction")
    alert = parse_alerts({"features": [feature]}, 1)[0]

    assert alert.attributes["nws_code"] == "None"
    assert alert.attributes["same_code"] == "None"
    assert alert.attributes["affected_zones"] == "None"
    assert alert.attributes["instruction"] == "None"


def test_active_alert_list_attributes_are_scalar_values() -> None:
    """The aggregate list sensor should expose readable scalar attributes."""
    alerts = parse_alerts(
        {
            "features": [
                _feature("one", "Severe"),
                _feature("two", "Moderate"),
            ]
        },
        10,
    )

    attributes = active_alert_list_attributes(alerts)

    assert attributes["alert_code"] == "TOR, TOR"
    assert attributes["alert_severity"] == "Severe, Moderate"
    assert attributes["alert_message"] == "Take cover.\n\nTake cover."
    assert not any(isinstance(value, list) for value in attributes.values())


def test_active_alert_list_attributes_use_none_when_empty() -> None:
    """Empty aggregate details should remain visible in Home Assistant."""
    attributes = active_alert_list_attributes(())

    assert attributes == {
        "alert_code": "None",
        "alert_severity": "None",
        "alert_message": "None",
    }
