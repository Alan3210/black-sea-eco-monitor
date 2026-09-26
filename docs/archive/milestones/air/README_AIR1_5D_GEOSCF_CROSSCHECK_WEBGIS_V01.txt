AIR-1.5D — GEOS-CF + Model Cross-Check Web GIS v0.1
====================================================

Purpose
-------
Expose the completed AIR-1.5 backend functionality in the operator Web GIS.

New atmosphere order
--------------------
CAMS
Sentinel-5P / TROPOMI
NASA GEOS-CF v2
CAMS ↔ GEOS-CF model cross-check
Drift Forecast

GEOS-CF map layer
-----------------
Endpoint:
  GET /air/geos-cf-field

UI products:
  PM2.5
  PM10

Default:
  time_index=0
  stride=1

Displays:
  MIN / MEAN / MAX
  robust P5/P25/P50/P75/P95 color scale
  run time
  valid time
  run age
  opacity
  exact clicked model-cell concentration

The layer is separate from CAMS so an operator can visually inspect each
model independently.

Model cross-check panel
-----------------------
Endpoint:
  GET /air/model-crosscheck

Uses the selected PM2.5 / PM10 product.

Displays:
  time gap
  comparison coverage
  GEOS-CF mean
  CAMS mean
  bias GEOS-CF - CAMS
  MAE
  RMSE
  Pearson r

Scientific semantics
--------------------
GEOS-CF is a research model forecast.

The comparison is model-to-model only:
- neither model is ground truth
- no regulatory interpretation
- no automatic "agreement" / "disagreement" verdict
- classification remains "not_calibrated"

Frontend tests
--------------
cd frontend
npm test

Production build
----------------
npm run build
