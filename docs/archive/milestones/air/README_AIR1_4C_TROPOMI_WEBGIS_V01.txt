AIR-1.4C — TROPOMI Web GIS v0.1
================================

Purpose
-------
Add an operational Sentinel-5P/TROPOMI satellite observation layer to
the existing Web GIS.

Production behavior
-------------------
Endpoint:
  GET /air/satellite-field

Default:
  product=no2
  timeliness=NRTI
  stride=2
  lookback_days=7

The API already resolves latest available non-empty TROPOMI coverage.

Visualization
-------------
- only valid satellite pixels are rendered
- dataMask/null pixels are absent
- polygon cells are built from canonical pixel-centre coordinates
- relative robust color scale uses P5/P25/P50/P75/P95
- no safe/dangerous semantic labels
- opacity control
- resolved satellite date
- coverage percentage
- MIN / P50 / MAX
- click a cell -> exact selected value in the panel
- selectable products:
  NO2, SO2, CO, O3, CH4, HCHO, two aerosol-index products

Display unit rule
-----------------
Canonical API remains unchanged.

For readability only, UI displays mol/m^2 products as micromol/m^2:
  displayed = raw mol/m^2 * 1e6

CH4 remains ppb.
Aerosol Index remains dimensionless.

Scientific disclaimer
---------------------
Sentinel-5P/TROPOMI is a satellite column/aerosol retrieval.
It is not a surface concentration, not a station measurement, and not
a CAMS forecast.

The color scale is relative to the selected field P5-P95 and is NOT an
air-quality threshold scale.

Frontend tests
--------------
cd frontend
npm test

Build
-----
npm run build
