WEATHER-1.5B — Web GIS ECMWF Wind Arrows v0.1
================================================

Purpose
-------
Visualize the WEATHER-1.5A ECMWF IFS 10 m wind field in Web GIS.

This stage adds arrows only. Animated wind particles remain WEATHER-1.5C.

UI
--
New independent ATMOSPHERE section:
- Wind · 10 m · ECMWF IFS toggle
- wind arrow size slider
- live model time / vector count / forecast run
- explicit wind-direction semantics

Map
---
The arrow glyph is north-oriented before MapLibre rotation.

MapLibre rotation uses:
  direction_to_deg

This is deliberately different from meteorological wind direction:
  direction_from_deg

Example:
  wind FROM 30°
  arrow points TO 210°

Strength
--------
Arrow size and opacity are functions of speed_ms.

Popup
-----
Clicking a wind arrow shows:
- wind speed
- meteorological FROM direction
- physical TO direction
- u/v components
- height (10 m)
- valid/model time
- ECMWF forecast run
- source/mirror

Data source
-----------
GET /weather/wind-field?stride=2

The frontend uses the WEATHER-1.5A endpoint and therefore visualizes the
same ECMWF IFS forcing family used by currents_plus_wind OpenDrift mode.

Vite
----
The installer adds /weather -> http://127.0.0.1:8000 proxy if it is not
already present.

Scope / scientific limits
-------------------------
This is a wind-field visualization layer.
It does not change:
- Copernicus currents
- OpenDrift physics
- windage = 2% configuration
- Stokes drift
- oil weathering
- Impact Screening

Install
-------
Expand the ZIP into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  python .\tools\install_weather1_5b_webgis_wind_arrows_v01.py

Targeted frontend test
----------------------
  cd .\frontend
  npm test -- --run src/wind.test.js

The project's npm test script runs the full src/*.test.js suite; the
expected total will therefore be the previous 79 tests plus 9 new wind
tests = 88 tests, assuming no other test files were added.

Build
-----
  npm run build

Live UI validation
------------------
1. Start backend and frontend.
2. Open http://127.0.0.1:5173/
3. Enable ATMOSPHERE -> Wind · 10 m · ECMWF IFS.
4. Confirm blue/cyan arrows appear.
5. Confirm arrow sizes vary with wind speed.
6. Click an arrow.
7. Confirm FROM and TO differ by exactly 180°.
8. Confirm ECMWF model time, forecast run, source, and 10 m height are shown.

Rollback
--------
Installer backups are written to dev-snapshots with:
  before_weather1_5b_<timestamp>

Git
---
After validation, stage only WEATHER-1.5B files.
