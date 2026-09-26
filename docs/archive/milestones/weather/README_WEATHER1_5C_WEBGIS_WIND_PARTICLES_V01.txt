WEATHER-1.5C — Web GIS ECMWF Wind Particles v0.1
===================================================

Purpose
-------
Add an animated wind-flow layer driven by the same normalized ECMWF IFS
10 m vector field already used by WEATHER-1.5B arrows.

Modes
-----
ATMOSPHERE -> Display:
- Arrows
- Particles
- Arrows + particles

Default remains:
- Arrows

Controls
--------
- Particle count: 400..2400
- Animation speed: 50..200%
- Trail length: 10..100%

Scientific / visual semantics
-----------------------------
Particles advect using u/v wind components.

The particle animation is a visualization acceleration, not real-time air
parcel timing. A dedicated wind visual time scale is used because 10 m
wind speeds are much larger than ocean current speeds.

This does not change OpenDrift physics or windage. It only visualizes the
ECMWF wind field already exposed by /weather/wind-field.

Performance
-----------
The default particle count adapts to navigator.hardwareConcurrency:
- <= 4 logical cores: 700
- <= 8 logical cores: 1000
- otherwise: 1400

Animation pauses while:
- the browser tab is hidden;
- the map is moving.

The canvas is non-interactive (pointer-events: none), so MapLibre arrow
clicks/popups remain usable in "Arrows + particles" mode.

Install
-------
Expand ZIP into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  python .\tools\install_weather1_5c_webgis_wind_particles_v01.py

Tests
-----
  cd .\frontend
  npm test -- --run src/windParticles.test.js

The project npm script runs all src/*.test.js files.
Expected total after WEATHER-1.5C:
  tests 99
  pass 99
  fail 0

Build
-----
  npm run build

Live validation
---------------
1. Start backend/frontend.
2. Enable ATMOSPHERE -> Wind.
3. Select "Particles".
4. Confirm cyan particle flow is animated.
5. Select "Arrows + particles".
6. Confirm both arrow field and particles coexist.
7. Pan/zoom the map:
   - particles pause during movement;
   - particles resume after moveend.
8. Change particle count, animation speed, and trail length.
9. Reload page and confirm selected display/settings persist.
10. Click an arrow in "Arrows + particles" mode and confirm the existing
    ECMWF popup still works.

Scope
-----
Frontend-only visualization stage.

No changes to:
- WEATHER-1.5A API
- ECMWF data retrieval
- Copernicus currents
- OpenDrift forcing
- direct windage = 2%
- Stokes drift
- oil weathering
- Impact Screening
