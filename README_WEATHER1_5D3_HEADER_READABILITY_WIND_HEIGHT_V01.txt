WEATHER-1.5D.3 — Header Readability + Wind Height v0.1
===========================================================

Live findings
-------------
1. The WEATHER-1.5D.2 header integration works and saves map space.
2. Operational metadata is too small for comfortable reading.
3. "Wind · 10 m" is ambiguous to non-meteorological users.

Important terminology
---------------------
"10 m" does NOT mean 10 metres per second.

It is the standard reference HEIGHT above the surface at which the
ECMWF 10 m wind field is defined.

Wind speed remains a separate quantity and is displayed in m/s.

UI wording
----------
Russian:
  Ветер · высота 10 м
  Ветер · высота 10 м · ECMWF IFS

English:
  Wind · height 10 m
  Wind · height 10 m · ECMWF IFS

The atmosphere note explicitly explains:
  10 м — высота над поверхностью, не скорость ветра.

Readability changes
-------------------
- combined header width increased;
- field-title typography increased;
- source/time typography increased;
- display-mode typography increased;
- Delta-t typography increased;
- summary/status typography increased;
- field cards and identity bars slightly enlarged;
- responsive widths rebalanced.

Scientific scope
----------------
Frontend wording/layout only.

No changes to:
- wind speed values;
- u/v vectors;
- ECMWF wind field;
- Copernicus currents;
- timestamps;
- OpenDrift;
- windage;
- impact analysis;
- any backend endpoint.

Install
-------
Extract into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  python .\tools\install_weather1_5d3_header_readability_wind_height_v01.py

Regression
----------
No JavaScript logic changed.

Expected existing frontend regression:
  tests 112
  pass 112
  fail 0

Then:
  npm run build

Live validation
---------------
1. Ctrl+F5.
2. Enable currents + wind.
3. Confirm top-bar metadata is comfortably readable.
4. Confirm wind label says:
     Ветер · высота 10 м
5. Confirm atmosphere sidebar says:
     Ветер · высота 10 м · ECMWF IFS
6. Confirm note explains that 10 m is height, not speed.
