EkoKontur — GEE Sentinel-1 Access Probe v0.1

Replace:
  tools/gee_access_probe.py

Run from repository root with an active venv and GEE_PROJECT_ID set:

  python tools\gee_access_probe.py

Expected compact output:
  Earth Engine initialization: OK
  Dataset: COPERNICUS/S1_GRD
  AOI: Novorossiysk
  Matching scenes: N
  Saved scene metadata: 5
  Output: validation\gee_sentinel1_probe.json
  Probe completed successfully.

The script:
- does not modify FastAPI;
- does not write to events.db;
- does not run anomaly detection;
- does not export raster imagery;
- only validates Earth Engine access and saves compact Sentinel-1 scene metadata.
