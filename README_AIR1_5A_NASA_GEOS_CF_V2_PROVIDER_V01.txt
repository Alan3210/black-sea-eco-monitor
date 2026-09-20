AIR-1.5A — NASA GEOS-CF v2 Provider v0.1
=========================================

Purpose
-------
Add NASA GEOS-CF v2 as the second independent atmospheric MODEL source
for future CAMS cross-check / fallback logic.

Official source
---------------
NASA GMAO / NASA Center for Climate Simulation (NCCS) public OPeNDAP.

Dataset:
  GEOS-CF v2
  forecast
  aqc_tavg_1hr_glo_L1440x721_slv.latest

Characteristics
---------------
- global 0.25 degree grid
- hourly-average surface-layer air-quality collection
- 120 hourly forecast fields (~5 days)
- default project subset:
  [west, south, east, north]
  [26.0, 39.0, 43.5, 48.0]

Products
--------
pm25 -> pm25_rh35 -> µg/m³
pm10 -> pm10_rh35 -> µg/m³
no2  -> no2       -> mol/mol dry air
so2  -> so2       -> mol/mol dry air
o3   -> o3        -> mol/mol dry air
co   -> co        -> mol/mol dry air

Important cross-check rule
--------------------------
PM2.5 and PM10 have native mass-concentration units compatible with
CAMS µg/m³ for later numerical comparison.

GEOS-CF NO2/SO2/O3/CO are native dry-air mole fractions (mol/mol).
They must NOT be numerically compared with CAMS µg/m³ until a physically
explicit unit-conversion step is implemented.

Semantics
---------
GEOS-CF = model_forecast
GEOS-CF != observation
GEOS-CF != station measurement
GEOS-CF != satellite observation

It is a NASA research product, not a regulatory compliance measurement.

Dependency
----------
backend/requirements-air.txt:
  pydap>=3.5,<4

Install dependency after package installation:
  python -m pip install -r backend/requirements-air.txt

Targeted tests
--------------
python -m pytest -q tests/test_geos_cf_provider.py

Live probe
----------
python -m tools.air1_5a_geos_cf_probe --product pm25 --time-index 0 --stride 1

Cache
-----
data/cache/air/geos-cf-v2/<product>/<run>/
