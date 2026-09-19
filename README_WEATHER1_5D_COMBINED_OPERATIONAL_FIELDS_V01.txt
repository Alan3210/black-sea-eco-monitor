WEATHER-1.5D — Combined Operational Wind + Current Visualization v0.1
====================================================================

Purpose
-------
Make simultaneous Copernicus surface-current and ECMWF 10 m wind
visualization operationally unambiguous without changing either physical
field or any forecast physics.

UI behavior
-----------
The combined HUD appears only when BOTH layers are enabled.

It shows:
- Currents: Copernicus Marine identity, active display mode, valid time.
- Wind: ECMWF IFS / 10 m identity, active display mode, valid time.
- Δt: absolute difference between the two valid timestamps.
- Explicit semantic lock:
    "Independent fields · not a resultant vector"

Visual identity
---------------
- Currents: yellow/orange swatch, matching current particle/arrow language.
- Wind: ice-cyan swatch with dark outline, matching wind particles.

Important semantics
-------------------
This stage does NOT:
- add current and wind vectors together;
- change windage;
- change OpenDrift;
- change ECMWF or Copernicus interpolation;
- change any backend API;
- imply that equal/near valid times mean the fields are physically fused.

Δt is descriptive only.

Install
-------
Extract into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  python .\tools\install_weather1_5d_combined_operational_fields_v01.py

Targeted test
-------------
  cd .\frontend
  npm test -- --run src/combinedFields.test.js

Expected targeted module:
  7 passed / 0 failed

Full frontend regression
------------------------
Current baseline is 105 tests.
WEATHER-1.5D adds 7 tests.

Expected:
  tests 112
  pass 112
  fail 0

Then:
  npm run build

Live validation
---------------
1. Enable only currents:
   - combined HUD must remain hidden.

2. Enable only wind:
   - combined HUD must remain hidden.

3. Enable BOTH:
   - HUD appears;
   - both field identities are distinct;
   - valid time for each field is shown separately;
   - display modes update when changed;
   - Δt updates after field refresh;
   - explicit "not a resultant vector" note is visible.

4. Disable either layer:
   - HUD disappears immediately.

Scientific scope
----------------
Frontend operational visualization only.
No backend or numerical-model changes.
