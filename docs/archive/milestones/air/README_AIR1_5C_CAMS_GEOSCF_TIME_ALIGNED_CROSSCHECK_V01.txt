AIR-1.5C — CAMS / GEOS-CF Time-Aligned Cross-Check v0.1
========================================================

Purpose
-------
Perform a scientifically explicit model-to-model cross-check between:
- CAMS Europe ensemble
- NASA GEOS-CF v2

REAL API
--------
GET /air/model-crosscheck

Query:
  product=pm25|pm10
  geos_time_index=0..119
  geos_stride=1..8
  cams_stride=1..8
  max_time_gap_minutes=0..180

Current supported products
--------------------------
PM2.5 and PM10 only.

Why gases are excluded:
GEOS-CF NO2/SO2/O3/CO are mol/mol while current CAMS fields are mass
concentration. AIR-1.5C does not silently convert them.

Time alignment
--------------
GEOS-CF hourly-average valid times are centred on the half hour.
CAMS valid times are hourly.

AIR-1.5C:
1. takes GEOS-CF valid_time
2. chooses the nearest CAMS whole UTC hour
3. requests CAMS for that date/hour
4. verifies the ACTUAL returned CAMS valid_time
5. rejects comparison when absolute gap exceeds the configured limit

Default:
  max_time_gap_minutes = 45

Spatial alignment
-----------------
Reference grid:
  GEOS-CF 0.25 degree grid

CAMS is bilinearly interpolated onto GEOS-CF cell centres.

No comparison value is created if any of the four CAMS interpolation
corners is invalid.

Metrics
-------
bias_geos_minus_cams
mae
median_absolute_difference
rmse
pearson_r
symmetric_mean_absolute_relative_difference_percent

Difference-grid convention:
  GEOS-CF - CAMS

Scientific semantics
--------------------
Neither CAMS nor GEOS-CF is ground truth.

This stage deliberately does NOT classify:
- agreement
- disagreement
- good/bad model
- preferred model

Response:
  agreement_classification = "not_calibrated"

Threshold-based classification should only be added after calibration and
validation against independent evidence.

Targeted tests
--------------
python -m pytest -q tests/test_air_model_crosscheck.py

Live probe
----------
python -m tools.air1_5c_model_crosscheck_probe --product pm25
