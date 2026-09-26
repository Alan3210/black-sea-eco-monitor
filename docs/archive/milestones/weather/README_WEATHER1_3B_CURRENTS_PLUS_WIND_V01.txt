WEATHER-1.3B Currents + Wind in OceanDrift v0.1

Purpose
-------
Add an explicit optional currents+wind mode to the existing OceanDrift
passive-surface-tracer forecast.

Modes
-----
current_only
    Existing baseline. This remains the default for backward compatibility.
    wind_drift_factor = 0.0

currents_plus_wind
    Copernicus Marine uo/vo + ECMWF IFS x_wind/y_wind.
    OceanDrift direct windage = 0.02.
    Stokes drift remains disabled.

Scientific semantics
--------------------
This is still a generic passive surface tracer with direct windage.
It is NOT a full oil-spill forecast and does NOT include:
- waves / Stokes drift;
- oil weathering;
- evaporation;
- emulsification;
- viscosity changes.

The 0.02 wind_drift_factor is applied by OpenDrift itself. No manual
"current + N% wind" vector arithmetic is implemented outside OpenDrift.

API
---
GET /ocean/drift/?...&forcing_mode=current_only
GET /ocean/drift/?...&forcing_mode=currents_plus_wind

The existing frontend sends no forcing_mode, therefore it remains current-only
until a later UI stage explicitly exposes the new mode.

Payload
-------
The drift payload keeps the existing Copernicus forcing fields and adds:
forcing.wind
with ECMWF run, steps, mirror source, bbox and fallback provenance.

Cache keys now include forcing_mode so current-only and wind-enabled runs can
never collide.

Install
-------
python .\tools\install_weather1_3b_currents_plus_wind_v01.py

Targeted tests
--------------
python -m pytest -q .\tests\test_ocean_drift_wind_mode.py

Live probe
----------
python .\tools\weather1_3b_drift_wind_probe.py --lon 37.8 --lat 44.6 --hours 6 --particles 100
