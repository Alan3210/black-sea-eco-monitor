AIR-1.4B — Canonical Sentinel-5P Satellite Field API v0.1.1
============================================================

Prerequisite
------------
AIR-1.4A must already be installed:
backend/services/sentinel5p_provider.py

REAL API
--------
GET /air/satellite-field

Query
-----
product=no2
date=YYYY-MM-DD
timeliness=NRTI|OFFL|RPRO
stride=1..8

Canonical rules
---------------
- Sentinel-5P / TROPOMI L2
- semantics.kind = satellite_observation
- NOT a CAMS forecast
- NOT a station measurement
- NOT a surface concentration
- raw scientific values preserved, including valid negative retrievals
- dataMask<=0 or non-finite value -> JSON null
- latitude[] ascending
- longitude[] ascending
- coordinates are pixel centres
- stride skips pixels only; no interpolation

Statistics
----------
statistics:
  full valid source raster before stride

returned_grid_statistics:
  valid values returned after stride

Observed real Black Sea NO2 raster
----------------------------------
350 x 180
2 float32 bands
EPSG:4326
bbox [26.0, 39.0, 43.5, 48.0]
Process API output spacing 0.05 deg x 0.05 deg
valid coverage 58.98095238095238%

0.05 deg is the configured Process API OUTPUT GRID spacing.
It is not native TROPOMI spatial resolution.

Dependency
----------
backend/requirements-air.txt records:
rasterio>=1.5.1,<2

Targeted test
-------------
python -m pytest -q tests/test_sentinel5p_satellite_field.py
