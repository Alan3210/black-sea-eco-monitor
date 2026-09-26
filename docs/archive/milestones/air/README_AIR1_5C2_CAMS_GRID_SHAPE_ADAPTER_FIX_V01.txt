AIR-1.5C.2 — CAMS Grid Shape Adapter Fix v0.1
==============================================

Confirmed live CAMS grid schema
-------------------------------
grid.latitude_order = ascending
grid.longitude_order = ascending
grid.stride = 1
grid.latitudes = array length 90
grid.longitudes = array length 175
grid.values = matrix 90 x 175
grid.shape = [90, 175]

The previous adapter looked for:
  grid.latitude
  grid.longitude

which returned empty axes and caused:
  Canonical field row count does not match latitude.

Fix
---
The cross-check adapter now accepts both singular and plural aliases:

  latitude / latitudes
  longitude / longitudes

at both top level and under grid.

No changes to:
- time alignment
- bilinear interpolation
- metric definitions
- unit normalization
- agreement semantics
- source data

Tests
-----
python -m pytest -q \
  tests/test_air_model_crosscheck.py \
  tests/test_air_model_crosscheck_schema.py \
  tests/test_air_model_crosscheck_grid_shape.py

Expected total for these files:
  17 passed

Then repeat the live AIR-1.5C probe.
