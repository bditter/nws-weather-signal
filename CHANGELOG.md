# Changelog

## 1.0.0 - 2026-06-14

- Initial public release.
- Add 1 to 10 stable binary-sensor alert slots.
- Normalize Home Assistant number-selector values to valid integer slot counts.
- Keep the complete alert attribute schema on inactive slots.
- Allow coordinates, zone/county, state/area, and location method changes from
  integration options.
- Make location-option retries safe after validation errors.
- Add configured query, alert count, last update, and polling interval
  attributes for troubleshooting.
- Return NWS code, SAME code, and affected zones as scalar strings instead of
  lists.
- Use the visible string `None` for every inactive or missing alert attribute.
- Support coordinate, NWS zone/county, and state/area lookups.
- Expose NWS/SAME codes and detailed CAP alert attributes.
- Add UI configuration and editable alert-slot options.
- Add original project artwork and HACS brand assets.
- Add summary active-alert and active-alert-list entities.
