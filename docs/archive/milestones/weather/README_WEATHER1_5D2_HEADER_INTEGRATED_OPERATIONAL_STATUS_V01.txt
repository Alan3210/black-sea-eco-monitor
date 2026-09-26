WEATHER-1.5D.2 — Header-Integrated Operational Status v0.1
=================================================================

Why this replaces the floating HUD
----------------------------------
Live validation of WEATHER-1.5D showed that the operational wind/current
HUD competes with the map and can be obscured by the application's fixed
top bar.

WEATHER-1.5D.2 moves the same operational information into the existing
top bar. This preserves map area and makes field provenance/status behave
like application-level telemetry.

What is shown when BOTH layers are enabled
------------------------------------------
CURRENT:
- orange/yellow identity bar;
- Copernicus Marine;
- current field valid time;
- active current display mode.

WIND:
- ice-cyan identity bar;
- ECMWF IFS;
- wind field valid time;
- active wind display mode.

SUMMARY:
- combined-mode state;
- absolute Δt between the two valid timestamps;
- explicit semantic lock:
  "Independent fields · not a resultant vector".

Visibility
----------
The block appears only when BOTH surface currents and wind are enabled.
If either layer is disabled, the top bar returns to its normal compact
state.

Responsive behavior
-------------------
- Full operational information on wide desktop layouts.
- Display-mode and semantics text are progressively hidden on narrower
  desktop widths.
- The combined block is hidden below 900 px so language and connection
  controls keep priority.

Scientific scope
----------------
Frontend layout only.

NO changes to:
- backend APIs;
- ECMWF wind data;
- Copernicus currents;
- field valid times;
- bilinear wind particle interpolation;
- OpenDrift;
- direct windage;
- Stokes drift;
- impact analysis.

IMPORTANT
---------
This patch expects the clean WEATHER-1.5D baseline.
Do NOT install WEATHER-1.5D.1 first.

Install
-------
Extract into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  python .\tools\install_weather1_5d2_header_integrated_operational_status_v01.py

Regression
----------
No JavaScript logic changed. Existing WEATHER-1.5D tests remain applicable.

Expected full frontend regression:
  tests 112
  pass 112
  fail 0

Then:
  npm run build

Live validation
---------------
1. Ctrl+F5.
2. Enable only currents:
   combined top-bar block remains hidden.
3. Enable only wind:
   combined top-bar block remains hidden.
4. Enable both:
   combined block appears INSIDE the fixed top bar.
5. Verify:
   - Copernicus and ECMWF are visually distinct;
   - both valid times are readable;
   - Δt is visible;
   - "not a resultant vector" semantics are present;
   - map has no floating combined HUD.
6. Disable either layer:
   combined block disappears.
