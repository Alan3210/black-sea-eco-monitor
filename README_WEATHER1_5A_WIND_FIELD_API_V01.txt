WEATHER-1.5A — ECMWF Wind Field API v0.1

Adds:
GET /weather/wind-field?at=<ISO8601>&stride=1..8

Default stride: 2.

Each vector contains:
latitude, longitude, u_ms, v_ms, speed_ms,
direction_from_deg, direction_to_deg.

direction_from_deg is meteorological FROM.
direction_to_deg is physical motion TO and is intended for a
north-up MapLibre arrow.

The field is linearly interpolated to the requested valid time from
the same WEATHER-1.3A ECMWF IFS wind-cube pipeline used by OpenDrift.

No frontend, OceanDrift physics, or impact logic is modified.

Install:
python .\tools\install_weather1_5a_wind_field_api_v01.py

Targeted tests:
python -m pytest -q .\tests\test_wind_field_service.py .\tests\test_wind_field_api.py

Live probe:
python .\tools\weather1_5a_wind_field_probe.py --stride 2
