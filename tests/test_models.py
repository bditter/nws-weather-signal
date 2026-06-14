"""Tests for NWS alert normalization."""

from custom_components.nws_weather_signal.models import parse_alerts


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
    assert alert.attributes["nws_code"] == ["TOR"]
    assert alert.attributes["same_code"] == ["TOR"]
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
