AIR-1.4A — Sentinel-5P / TROPOMI Provider v0.1
================================================

Purpose
-------
Add a real Copernicus Sentinel-5P/TROPOMI Level-2 satellite provider
for atmospheric evidence over the Black Sea region.

Official service
----------------
Copernicus Data Space Ecosystem / Sentinel Hub Process API.

Authentication
--------------
Create an OAuth client in the Copernicus Data Space Ecosystem
Sentinel Hub dashboard and expose credentials only through environment
variables:

  $env:CDSE_SH_CLIENT_ID="<client-id>"
  $env:CDSE_SH_CLIENT_SECRET="<client-secret>"

Never commit the secret.

Products
--------
- NO2: tropospheric column, mol/m^2
- SO2: total column, mol/m^2
- CO: total column, mol/m^2
- O3: total column, mol/m^2
- CH4: column averaged dry-air mixing ratio, ppb
- HCHO: tropospheric vertical column, mol/m^2
- AER_AI_340_380: UV aerosol index
- AER_AI_354_388: UV aerosol index

Scientific semantics
--------------------
Sentinel-5P/TROPOMI L2 is a SATELLITE OBSERVATION.

It is NOT:
- a CAMS forecast;
- a ground-station measurement;
- a surface pollutant concentration;
- a direct PM2.5 measurement.

Do not compare NO2/SO2/CO column values numerically with surface
ug/m3 station or CAMS surface fields as if they were the same quantity.

Quality / raster policy
-----------------------
- NO2 default minQa = 75%
- other products default minQa = 50%
- dataMask is returned as the second band
- FLOAT32 GeoTIFF
- NEAREST resampling
- request window <= 24 hours
- default Black Sea bbox is [west, south, east, north]:
  [26.0, 39.0, 43.5, 48.0]
- default output grid: 350 x 180

AIR-1.4A deliberately caches the scientific GeoTIFF and provenance
metadata first. Canonical JSON field parsing / Web GIS rendering belongs
to the next production step after a live file is validated.

Targeted tests
--------------
  pytest -q tests/test_sentinel5p_provider.py

Live probe
----------
  python -m tools.air1_4a_sentinel5p_probe --product no2 --hours 23.5 --timeliness NRTI

Cache
-----
  data/cache/air/sentinel5p/<product>/
