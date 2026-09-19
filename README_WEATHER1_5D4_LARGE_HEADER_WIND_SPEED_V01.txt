WEATHER-1.5D.4 — Large Header + Wind Speed v0.1
====================================================

Live feedback addressed
-----------------------
1. The combined operational header still used typography that was too
   small for comfortable reading.
2. Operator wants wind SPEED, not measurement-height metadata.

Wind-speed semantics
--------------------
A wind field is spatially variable, so there is no scientifically honest
single "the wind speed" for the entire visible/loaded field.

Therefore the header shows:
  ср. X.X м/с

This is the FIELD-WIDE MEAN speed reported by the existing
/weather/wind-field payload:
  speed_stats.mean_speed_ms

If backend speed statistics are unavailable, the frontend falls back to
the arithmetic mean of the normalized wind-vector speeds.

Exact LOCAL speed remains available by clicking a wind vector.

Primary operator wording
------------------------
Header:
  Ветер
  ср. X.X м/с
  ECMWF IFS · <valid time>

Atmosphere sidebar:
  Ветер · ECMWF IFS

No "height 10 m" wording is shown in the primary operator UI.

Readability changes
-------------------
- top bar min-height: 104 px;
- combined operational block wider;
- field titles: 14 px;
- field metadata: 10.5 px;
- field display modes: 11 px;
- wind mean-speed line: 15 px;
- Delta-t: 13 px;
- status/semantic text enlarged;
- filter and event panels moved down to clear the taller top bar.

Scientific scope
----------------
No backend or physical-model changes.

Unchanged:
- ECMWF u/v and speed values;
- /weather/wind-field;
- Copernicus currents;
- wind-particle interpolation;
- OpenDrift;
- direct windage;
- impact screening.

Install
-------
Extract into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  python .\tools\install_weather1_5d4_large_header_wind_speed_v01.py

Targeted regression
-------------------
  cd .\frontend
  npm test -- --run src/combinedFields.test.js

WEATHER-1.5D.4 adds 4 combined-field tests.

Expected full frontend regression:
  tests 116
  pass 116
  fail 0

Then:
  npm run build

Live validation
---------------
1. Ctrl+F5.
2. Enable currents + wind.
3. Confirm the fixed top bar is visibly taller and easier to read.
4. Wind card must show:
     Ветер
     ср. <number> м/с
5. Confirm the value changes when a newly refreshed ECMWF field has a
   different mean wind speed.
6. Click a wind vector and confirm exact LOCAL speed is still shown.
7. Confirm the sidebar no longer emphasizes "height 10 m".
