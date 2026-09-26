AIR-1.3A.1 — CAMS NetCDF Inspector v0.1
=======================================

Purpose
-------
Inspect the FIRST REAL CAMS Europe artifact before defining the canonical
Air Field API.

The tool auto-detects the newest cached:
  ENS_FORECAST.nc
or any *.nc under:
  data/cache/air/cams-europe/

It writes the detailed inspection to:
  validation/air1_3a1_cams_netcdf_inspection.json

It prints a compact summary containing:
- dimensions
- coordinate names
- latitude/longitude orientation
- time coordinate
- level coordinate if present
- all data variable names
- variable dims/shapes
- units
- long_name / standard_name
- finite min/max/mean
- file size

This stage intentionally does NOT rename or canonicalise real CAMS
variables. The inspection output is the authority for AIR-1.3B.

Install
-------
Extract into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  .\backend\venv\Scripts\Activate.ps1
  python .\tools\install_air1_3a1_cams_netcdf_inspector_v01.py

Targeted test:
  pytest tests/test_cams_netcdf_inspection.py

Run real inspection:
  python -m tools.air1_3a1_inspect_netcdf

Do not paste Python "from ..." statements directly into PowerShell.
