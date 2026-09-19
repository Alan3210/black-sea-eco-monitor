WEATHER-1.5C.1 — Viewport Wind Particles Fix v0.1
====================================================

Observed live symptom
---------------------
The wind particle mode was selected and controls were active, but the
particle flow was not visually apparent.

Browser diagnostics proved:
- wind-particles-canvas exists;
- display = block;
- visibility = visible;
- opacity = 1;
- z-index = 3;
- canvas is after the MapLibre canvas;
- the canvas was actually drawing pixels.

Measured example:
- particlePixels: 10298
- alpha >= 32: 62 pixels
- alpha >= 128: 9 pixels
- max alpha: 180

Root cause
----------
WEATHER-1.5C v0.1 seeded all particles uniformly from the full ECMWF
Black Sea vector field (420 vectors).

At a regional/local zoom such as Novorossiysk, only a small fraction of
the particle population was inside the visible viewport. The engine was
working, but almost all particles were off-screen.

Fix
---
1. Particle spawning is now viewport-aware:
   - intersect the current MapLibre bounds with the ECMWF field extent;
   - distribute new particles uniformly within the visible area;
   - verify that each seed is covered by a nearby wind vector.

2. On moveend, main.js already calls WindParticleEngine.resize().
   resize() now reseeds the population so a newly panned/zoomed viewport
   immediately receives a full particle population.

3. Particle strokes are made slightly brighter/wider for map readability.

Scientific scope
----------------
This is visual-density/rendering logic only.

No changes to:
- ECMWF u/v data;
- /weather/wind-field;
- OpenDrift;
- direct windage = 2%;
- Copernicus currents;
- Stokes drift;
- oil weathering;
- Impact Screening.

Install
-------
Expand ZIP into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  python .\tools\install_weather1_5c1_viewport_wind_particles_fix_v01.py

Tests
-----
  cd .\frontend
  npm test -- --run src/windParticles.test.js

The project npm script runs the full src/*.test.js suite.
Expected total after this patch:
  tests 100
  pass 100
  fail 0

Then:
  npm run build

Live validation
---------------
1. Ctrl+F5.
2. Enable ATMOSPHERE -> Wind.
3. Select Particles.
4. Confirm a dense animated cyan wind flow is visible in the current
   regional viewport.
5. Pan/zoom and confirm the particle population repopulates the new view.
6. Select Arrows + particles and confirm both coexist.
