WEATHER-1.5C.3 — Smooth Wind Particle Interpolation v0.1
==========================================================

Problem confirmed in live Web GIS
---------------------------------
Animated wind particles formed visible horizontal and vertical seams,
sometimes resembling incomplete rectangles.

Root cause in WEATHER-1.5C.2
----------------------------
Particle advection called sampleWindVector() at arbitrary lon/lat positions,
but sampleWindVector() selected one nearest ECMWF grid node.

That made u/v piecewise constant inside each grid cell. Long-lived particle
trails therefore exposed the regular latitude/longitude sampling grid.

Fix
---
For a complete regular wind grid:
- locate the four surrounding ECMWF vectors;
- bilinearly interpolate u and v at the particle lon/lat;
- recompute speed from interpolated u/v.

For a defensive incomplete/degenerate field:
- use inverse-distance weighted interpolation instead of hard nearest-neighbour.

Expected visual result
----------------------
- no horizontal/vertical cell seams in particle trails;
- trajectories change smoothly across grid-cell boundaries;
- arrows can remain on the regular grid by design;
- particles remain stochastic and continuous.

Scope
-----
Frontend visualization only.

Unchanged:
- ECMWF IFS source data;
- /weather/wind-field contract;
- wind-field stride;
- atmospheric valid time/run provenance;
- OpenDrift;
- direct windage = 2%;
- Copernicus currents;
- Stokes drift;
- Impact Screening.

Files modified
--------------
frontend/src/windParticles.js
frontend/src/windParticles.test.js

Install
-------
Extract this ZIP into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  python .\tools\install_weather1_5c3_smooth_wind_particle_interpolation_v01.py

Package self-test
-----------------
- installer simulation: PASS
- Node syntax: PASS
- windParticles.test.js: 16 passed / 0 failed

Live acceptance criterion
-------------------------
Use the same regional map view where the rectangular pattern was visible.

Atmosphere:
  Wind 10 m -> Particles

Wait 10-20 seconds.

PASS:
- particles show smooth trajectories;
- no regular horizontal/vertical incomplete rectangles remain.

If the pattern remains, capture the same viewport again before changing any
other wind settings.
