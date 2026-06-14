"""Data models and normalization for NWS Weather Signal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

_SEVERITY_RANK = {
    "Extreme": 0,
    "Severe": 1,
    "Moderate": 2,
    "Minor": 3,
    "Unknown": 4,
}
_URGENCY_RANK = {
    "Immediate": 0,
    "Expected": 1,
    "Future": 2,
    "Past": 3,
    "Unknown": 4,
}
_CERTAINTY_RANK = {
    "Observed": 0,
    "Likely": 1,
    "Possible": 2,
    "Unlikely": 3,
    "Unknown": 4,
}


def _as_strings(value: Any) -> tuple[str, ...]:
    """Normalize a CAP value to a tuple of strings."""
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item) for item in value if item is not None)
    return (str(value),)


def _event_codes(properties: dict[str, Any], key: str) -> tuple[str, ...]:
    """Read an event-code group from an alert."""
    event_code = properties.get("eventCode") or {}
    if not isinstance(event_code, dict):
        return ()
    return _as_strings(event_code.get(key))


@dataclass(frozen=True, slots=True)
class NwsAlert:
    """Normalized NWS alert."""

    alert_id: str
    event: str
    headline: str
    description: str
    instruction: str | None
    severity: str
    urgency: str
    certainty: str
    status: str
    message_type: str
    response: str | None
    area_description: str
    sent: str | None
    effective: str | None
    onset: str | None
    expires: str | None
    ends: str | None
    sender_name: str | None
    nws_codes: tuple[str, ...]
    same_codes: tuple[str, ...]
    affected_zones: tuple[str, ...]
    source_url: str

    @classmethod
    def from_feature(cls, feature: dict[str, Any]) -> NwsAlert:
        """Create an alert from a GeoJSON feature."""
        properties = feature.get("properties") or {}
        alert_id = str(properties.get("id") or feature.get("id") or "")
        event = str(properties.get("event") or "Weather alert")
        headline = str(properties.get("headline") or event)
        source_url = str(properties.get("@id") or feature.get("id") or "")

        return cls(
            alert_id=alert_id,
            event=event,
            headline=headline,
            description=str(properties.get("description") or ""),
            instruction=properties.get("instruction"),
            severity=str(properties.get("severity") or "Unknown"),
            urgency=str(properties.get("urgency") or "Unknown"),
            certainty=str(properties.get("certainty") or "Unknown"),
            status=str(properties.get("status") or "Unknown"),
            message_type=str(properties.get("messageType") or "Unknown"),
            response=properties.get("response"),
            area_description=str(properties.get("areaDesc") or ""),
            sent=properties.get("sent"),
            effective=properties.get("effective"),
            onset=properties.get("onset"),
            expires=properties.get("expires"),
            ends=properties.get("ends"),
            sender_name=properties.get("senderName"),
            nws_codes=_event_codes(properties, "NationalWeatherService"),
            same_codes=_event_codes(properties, "SAME"),
            affected_zones=_as_strings(properties.get("affectedZones")),
            source_url=source_url,
        )

    @property
    def sort_key(self) -> tuple[int, int, int, float, str]:
        """Sort the most consequential and newest alerts first."""
        try:
            sent_timestamp = datetime.fromisoformat(self.sent or "").timestamp()
        except ValueError:
            sent_timestamp = 0
        return (
            _SEVERITY_RANK.get(self.severity, 5),
            _URGENCY_RANK.get(self.urgency, 5),
            _CERTAINTY_RANK.get(self.certainty, 5),
            -sent_timestamp,
            self.alert_id,
        )

    @property
    def attributes(self) -> dict[str, Any]:
        """Return Home Assistant state attributes."""
        return {
            "title": self.headline,
            "event": self.event,
            "nws_code": list(self.nws_codes),
            "same_code": list(self.same_codes),
            "description": self.description,
            "instruction": self.instruction,
            "severity": self.severity,
            "urgency": self.urgency,
            "certainty": self.certainty,
            "status": self.status,
            "message_type": self.message_type,
            "recommended_response": self.response,
            "area_description": self.area_description,
            "sent": self.sent,
            "effective": self.effective,
            "onset": self.onset,
            "expires": self.expires,
            "ends": self.ends,
            "sender": self.sender_name,
            "affected_zones": list(self.affected_zones),
            "alert_id": self.alert_id,
            "source_url": self.source_url,
        }


def parse_alerts(payload: dict[str, Any], limit: int) -> tuple[NwsAlert, ...]:
    """Normalize, de-duplicate, prioritize, and limit an API response."""
    alerts: dict[str, NwsAlert] = {}
    for feature in payload.get("features") or []:
        if not isinstance(feature, dict):
            continue
        alert = NwsAlert.from_feature(feature)
        if alert.alert_id:
            alerts[alert.alert_id] = alert
    return tuple(sorted(alerts.values(), key=lambda alert: alert.sort_key)[:limit])
