AIR-1.4C.3 — TROPOMI Placement Fix v0.1
========================================

Problem confirmed from the real frontend DOM
---------------------------------------------
The TROPOMI host was inserted near the bottom of frontend/index.html,
after the Satellite/Legend content, instead of inside Atmosphere.

Observed order:
  CAMS
  Drift Forecast
  Satellite section
  ...
  TROPOMI root

Correct order:
  CAMS
  TROPOMI
  Drift Forecast

Fix
---
Only frontend/index.html is changed.

The existing:
  <div id="tropomi-air-root" class="tropomi-air-root"></div>

is removed from its misplaced location and inserted immediately before:
  <div class="drift-control">

No JavaScript, CSS, API, scientific logic, data handling or map rendering
is changed.

After install
-------------
cd frontend
npm test
npm run build

Then restart Vite / hard refresh and confirm that Sentinel-5P / TROPOMI
appears directly below CAMS and above Drift Forecast.
