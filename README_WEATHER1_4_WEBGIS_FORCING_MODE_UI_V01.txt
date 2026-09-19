WEATHER-1.4 Web GIS Forcing Mode UI v0.1
=========================================

Goal
----
Expose the WEATHER-1.3B backend forcing modes in Web GIS without changing
the established safe default.

UI modes
--------
1. Currents only
   - forcing_mode=current_only
   - Copernicus Marine surface currents
   - direct windage 0%
   - remains the default

2. Currents + wind
   - forcing_mode=currents_plus_wind
   - Copernicus Marine currents + ECMWF IFS 10 m wind
   - OpenDrift direct windage 2%

Scientific wording
------------------
The wind-enabled mode is still a generic passive surface tracer with direct
windage. The UI explicitly states that waves/Stokes drift and oil weathering
are not included and that this is not a full oil-spill forecast.

What the UI shows
-----------------
Before a wind-enabled run:
  Copernicus Marine + ECMWF IFS 10 m · direct windage 2%

After a successful wind-enabled run:
  ECMWF IFS forecast run
  mirror/source used
  direct windage percentage

State / safety
--------------
- forcing mode is persisted in localStorage;
- current_only remains the default;
- changing forcing mode invalidates the previous drift payload and impact
  screening so results from different physics cannot be mixed;
- the selected forcing_mode is always sent explicitly to /ocean/drift/.

Files modified
--------------
frontend/index.html
frontend/src/drift.js
frontend/src/main.js
frontend/src/i18n.js
frontend/src/style.css

File added
----------
frontend/src/driftForcing.test.js

Install
-------
python .\tools\install_weather1_4_webgis_forcing_mode_ui_v01.py

Targeted frontend test
----------------------
cd frontend
npm test -- --run src/driftForcing.test.js

Then run the full frontend regression and build before committing.
