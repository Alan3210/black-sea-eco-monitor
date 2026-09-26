AIR-1.5B — Canonical GEOS-CF Field API v0.1
============================================

Live AIR-1.5A result used for this stage
----------------------------------------
NASA GMAO GEOS-CF v2
PM2.5 / pm25_rh35
Black Sea grid 71 x 37
2,627 / 2,627 valid cells
100% valid coverage

Observed latest run at probe time:
  run_time       2026-09-19T09:00:00Z
  first_valid    2026-09-19T09:30:00Z
  valid_time     2026-09-19T09:30:00Z

Observed PM2.5:
  min   3.9140625
  mean  10.99974126855729
  p50   9.921875
  p95   19.66875
  max   42.375

REAL API
--------
GET /air/geos-cf-field

Query:
  product=pm25|pm10|no2|so2|o3|co
  time_index=0..119
  stride=1..8

New operational metadata
------------------------
freshness:
  evaluated_at
  run_age_hours
  valid_time_offset_hours_from_now
  valid_time_relation

These values are descriptive. AIR-1.5B does NOT yet invent a fallback
threshold.

cams_comparison:
  target_model
  unit_compatible
  direct_value_comparison_ready
  requires_valid_time_alignment
  requires_unit_conversion
  scientific_equivalence_assumed
  note

Important comparison policy
---------------------------
PM2.5 / PM10:
  GEOS-CF and CAMS both use mass-concentration units, so units are
  compatible. This does NOT mean the model variables are assumed
  scientifically identical. Direct cross-check is deliberately NOT enabled
  until AIR-1.5C aligns valid times and defines comparison metrics.

NO2 / SO2 / O3 / CO:
  GEOS-CF native unit is mol/mol.
  Current CAMS field is mass concentration.
  Explicit physical unit conversion is required first.

Windows output
--------------
The AIR-1.5B probe uses ASCII-safe JSON to avoid PowerShell legacy-codepage
corruption of symbols such as µ and ³.

Tests
-----
python -m pytest -q tests/test_geos_cf_field.py

Live canonical probe
--------------------
python -m tools.air1_5b_geos_cf_field_probe --product pm25 --time-index 0 --stride 1
