AIR-1.4A.1 — Sentinel-5P GeoTIFF Inspector v0.1
=================================================

Purpose
-------
Inspect the REAL cached Sentinel-5P/TROPOMI GeoTIFF before building the
canonical satellite field API.

The inspector reports:
- raster driver
- width/height
- band count
- dtype
- CRS
- geospatial bounds
- affine transform
- nodata
- dataMask values
- valid pixel coverage
- min/max/mean
- P05/P25/P50/P75/P95 on valid scientific pixels

Run
---
python -m tools.air1_4a1_sentinel5p_inspector --product no2

Output
------
validation/air1_4a1_sentinel5p_geotiff_inspection.json

Dependency
----------
Uses rasterio. If missing in the project venv:

pip install rasterio

Scientific rule
---------------
Band 1 must be interpreted using Band 2 dataMask. Statistics over the
scientific value band are computed only where dataMask > 0.
