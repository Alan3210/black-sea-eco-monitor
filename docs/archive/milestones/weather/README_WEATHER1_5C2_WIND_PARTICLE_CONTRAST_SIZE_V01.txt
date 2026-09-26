WEATHER-1.5C.2 — Wind Particle Contrast + Size v0.1
=====================================================

Live UI findings
----------------
After WEATHER-1.5C.1:
- particle animation works;
- viewport density works;
- particles are visible;
- however the cyan trails are too close to the pale water color;
- the visible "Arrow size" control is disabled in particle-only mode.

The disabled Arrow size slider is expected: arrows are hidden in
particle-only mode, so changing arrow size would have no visible effect.

Changes
-------
1. Particle contrast
   - bright ice-cyan core;
   - dark navy outline/halo behind each particle segment.

This preserves the wind/cyan visual language but keeps particles readable
over:
- pale blue water;
- green land;
- roads and labels.

2. Dedicated particle-size control
   New UI:
     Particle size / Размер частиц

   Range:
     60% .. 200%

   Default:
     120%

   This control is active in:
   - Particles
   - Arrows + particles

   Arrow size remains active only when arrows are visible.

3. Persistence
   Particle size is stored in localStorage:
     black-sea-eco-monitor.wind-particle-size

Scientific scope
----------------
Pure frontend visualization change.

No changes to:
- ECMWF u/v;
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
  python .\tools\install_weather1_5c2_wind_particle_contrast_size_v01.py

Tests
-----
  cd .\frontend
  npm test -- --run src/windParticles.test.js

Expected total:
  tests 102
  pass 102
  fail 0

Then:
  npm run build

Live validation
---------------
1. Ctrl+F5.
2. Enable Wind -> Particles.
3. Confirm particles have a high-contrast dark edge/halo and are clearly
   readable against the sea.
4. Confirm "Particle size" is active.
5. Change 60% -> 200% and verify particle width changes live.
6. Select Arrows + particles:
   - Arrow size becomes active;
   - Particle size remains active.
