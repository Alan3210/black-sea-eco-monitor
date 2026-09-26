WEATHER-1.5B.1 — Wind Render Fix v0.1
=======================================

Observed symptom
----------------
The ATMOSPHERE panel successfully reported a live ECMWF field such as:
  420 vectors
but no wind arrows appeared on the MapLibre map.

Root cause
----------
fetchWindField() already calls normalizeWindFieldPayload().

refreshWind() then passed that normalized payload to:
  windToFeatureCollection()

windToFeatureCollection() defensively called normalizeWindFieldPayload()
a second time.

Before this fix, normalizeWindFieldPayload() accepted only raw backend
component names:
  u_ms
  v_ms
  speed_ms

After the first normalization, vectors instead contain:
  u
  v
  speed

Therefore the second normalization rejected every vector as incomplete.
The UI status correctly displayed 420 vectors, while the GeoJSON source
received zero features.

Fix
---
normalizeWindFieldPayload() now accepts both:
  raw API:     u_ms / v_ms / speed_ms
  normalized:  u    / v    / speed

The function is now idempotent.

A regression test verifies:
  raw payload -> normalize -> normalize again -> GeoJSON
still produces the expected feature.

Install
-------
Expand this ZIP into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  python .\tools\install_weather1_5b1_wind_render_fix_v01.py

Targeted/full frontend tests
----------------------------
  cd .\frontend
  npm test -- --run src/wind.test.js

Because the project test script executes src/*.test.js, the expected total
after this patch is:
  tests 89
  pass 89
  fail 0

Then:
  npm run build

Live validation
---------------
Reload http://127.0.0.1:5173/
Enable:
  ATMOSPHERE -> Wind · 10 m · ECMWF IFS

Expected:
- wind arrows appear on the map;
- status still reports the ECMWF vector count;
- clicking an arrow opens the wind popup;
- FROM and TO differ by 180 degrees.
