AIR-1.3A — CAMS Europe Provider v0.1
====================================

Purpose
-------
Primary air-quality MODEL FORECAST provider for the Black Sea project.
No FastAPI endpoint or Web GIS layer is added yet.

Dataset
-------
CAMS European air quality forecasts
Dataset ID: cams-europe-air-quality-forecasts

Product
-------
- ENSEMBLE
- forecast
- 00 UTC run
- surface (ADS level 0)
- cropped Black Sea / Sea of Azov domain
- zipped NetCDF

Canonical species
-----------------
pm25 -> particulate_matter_2.5um
pm10 -> particulate_matter_10um
no2  -> nitrogen_dioxide
so2  -> sulphur_dioxide
o3   -> ozone
dust -> dust

PM2.5, PM10, NO2, SO2 and O3 are primary operational species.
Dust remains available but is tagged experimental in provider provenance.

Semantics
---------
CAMS field = model analysis/forecast field.
It is NOT a ground-station observation.

Default crop [North, West, South, East]
---------------------------------------
[48.0, 26.0, 39.0, 43.5]

Cache
-----
data/cache/air/cams-europe/

Each deterministic request stores:
- raw NetCDF ZIP
- extracted members
- metadata.json provenance
- SHA-256

ADS setup
---------
1. Login/register in the Atmosphere Data Store.
2. Accept the dataset Terms of Use for CAMS European air quality forecasts.
3. Create %USERPROFILE%\.cdsapirc with:

   url: https://ads.atmosphere.copernicus.eu/api
   key: <PERSONAL-ACCESS-TOKEN>

Never commit the token.

Install
-------
cd D:\repository\black-sea-eco-monitor
.\backend\venv\Scripts\Activate.ps1
python .\tools\install_air1_3a_cams_europe_provider_v01.py

Targeted tests
--------------
pytest tests/test_cams_air_quality_provider.py

Live probe
----------
python .\tools\air1_3a_cams_probe.py

AIR-1.3A.1 will inspect the first real downloaded NetCDF before we define
canonical /air/field decoding. This prevents us from guessing raw variable
names, longitude convention or time encoding.
