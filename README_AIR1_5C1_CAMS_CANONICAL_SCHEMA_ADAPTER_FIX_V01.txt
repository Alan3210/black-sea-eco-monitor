AIR-1.5C.1 — CAMS Canonical Schema Adapter Fix v0.1
====================================================

Live failure
------------
AIR-1.5C reached both live model sources successfully, then failed with:

  Unit mismatch: CAMS='', GEOS-CF='µg/m³'

Real CAMS canonical response
----------------------------
CAMS does NOT expose top-level:
  units
  unit
  source_variable
  longitude
  latitude
  values

Instead:

  pollutant.units
  pollutant.source_variable

and the field payload may be nested under:

  grid.longitude
  grid.latitude
  grid.values

Observed PM2.5 unit:
  CAMS    µg/m3
  GEOS-CF µg/m³

Fix
---
AIR-1.5C.1 adds a schema adapter that:
- reads units from top-level, pollutant, or semantics
- reads source_variable from top-level or pollutant
- reads longitude/latitude/values from top-level or grid
- normalizes spelling only:
    µg/m3
    µg/m³
    ug/m3
  -> canonical "ug/m3"

No physical unit conversion or concentration rescaling is performed.

The original AIR-1.5C tests remain valid.
Five new schema-adapter tests are added.

Tests
-----
python -m pytest -q \
  tests/test_air_model_crosscheck.py \
  tests/test_air_model_crosscheck_schema.py

Then repeat live probe:
python -m tools.air1_5c_model_crosscheck_probe \
  --product pm25 \
  --geos-time-index 0 \
  --geos-stride 1 \
  --cams-stride 1 \
  --max-time-gap-minutes 45
