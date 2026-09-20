AIR-1.3B — Canonical Air Field API v0.1
=======================================

Authority
---------
Built from the first REAL CAMS Europe NetCDF inspection.

Observed real schema:
- dimensions:
    time=3
    level=1
    latitude=90
    longitude=175
- time coordinate:
    0, 6, 12 forecast hours
- surface level:
    0 m
- latitude:
    descending in raw artifact
- longitude:
    ascending in raw artifact
- real variable names:
    pm2p5_conc
    no2_conc
    o3_conc
- concentration units:
    µg/m3

The canonical API normalises the raw latitude axis to ascending order.

Endpoint
--------
GET /air/field

Query:
  pollutant=pm25|pm10|no2|so2|o3|dust
  run_date=YYYY-MM-DD    optional
  lead_hour=0..96        optional
  stride=1..8            default 2

If run_date/lead_hour are omitted, AIR-1.3B selects a conservative
operational CAMS run and the current hourly lead.

Response semantics
------------------
CAMS is returned as:
  kind = model_forecast
  observation = false
  station_measurement = false

It MUST NOT be described as a station measurement.

Response contains:
- provider/dataset/model
- pollutant identity
- source CAMS variable
- units
- run_time
- lead_hour
- valid_time
- level_m
- canonical grid
- min/max/mean
- provenance

Grid
----
grid.latitudes
grid.longitudes
grid.values

Latitude and longitude are always canonical ascending axes.
grid.values[y][x] follows those two arrays.

Cache
-----
Before downloading, the service scans existing CAMS metadata sidecars
for a cached artifact containing:
- requested run date
- requested pollutant
- requested lead hour

This means the first AIR-1.3A live probe can be reused immediately.

Install
-------
Extract into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  .\backend\venv\Scripts\Activate.ps1
  python .\tools\install_air1_3b_canonical_air_field_api_v01.py

Targeted tests
--------------
  pytest tests/test_cams_air_field.py tests/test_air_field_api.py tests/test_air_field_router.py

Live API
--------
With uvicorn running:

  Invoke-RestMethod `
    "http://127.0.0.1:8000/air/field?pollutant=pm25&run_date=2026-09-19&lead_hour=6&stride=2" |
    ConvertTo-Json -Depth 6

The already-downloaded AIR-1.3A artifact contains pm25 at lead 6, so the
first validation should be served from cache without another ADS job.

Next
----
AIR-1.3C:
Web GIS concentration field / heatmap + pollutant selector + legend.
