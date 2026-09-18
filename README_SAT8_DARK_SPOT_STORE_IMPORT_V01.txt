EkoKontur — SAT-8 SAR Dark-Spot Candidate Store Import v0.1

Purpose
-------
Import reviewed-by-pipeline SAT-7B SAR dark-spot candidate polygons into
the canonical SatelliteObservation Store as separate derived observations.

This step stores candidate observations only.

It does NOT:
- create Events;
- update Events;
- create event↔satellite links;
- classify oil;
- confirm pollution;
- assign oil probability;
- assign confidence.

Input
-----
validation/gee_sentinel1_dark_spot_candidates_v01.json

Per-candidate storage mapping
-----------------------------
information_type = satellite_observation
derivation_level = derived
observation_type = sar_dark_spot_candidate

sensor = Sentinel-1
dataset_id = COPERNICUS/S1_GRD
source_image_id = source Sentinel-1 scene id
acquisition_time = source scene acquisition time

geometry = candidate MultiPolygon
bbox = candidate bbox
confidence = null
review_status = unreviewed

processing_version = extraction_version
processing_method = gee_sentinel1_dark_spot_candidates

Provenance preserves:
- candidate_id
- area_km2
- mean_vv_db
- threshold_db
- edge_noise_floor_db
- min_area_km2
- min_connected_pixels
- connectivity
- scale_meters
- water mask metadata
- source scene metadata
- source GEE provenance
- explicit semantic disclaimer

Idempotency
-----------
A candidate is treated as the same stored derived observation when all of
these match:

source_image_id
+ observation_type
+ processing_version
+ provenance.candidate_id

Re-running SAT-8 therefore does not duplicate already imported candidates.

Files
-----
backend/services/satellite/dark_spot_import.py
tools/import_sar_dark_spot_candidates_v01.py
tests/test_sar_dark_spot_candidate_import.py
README_SAT8_DARK_SPOT_STORE_IMPORT_V01.txt

Install
-------
Extract into repository root.
No existing source file is modified.

Syntax
------
python -m py_compile backend\services\satellite\dark_spot_import.py
python -m py_compile tools\import_sar_dark_spot_candidates_v01.py
python -m py_compile tests\test_sar_dark_spot_candidate_import.py

Targeted tests
--------------
python -m pytest -q tests\test_sar_dark_spot_candidate_import.py *> test-results\sat8_targeted.txt
Get-Content test-results\sat8_targeted.txt -Tail 30

Live canonical import
---------------------
Do this only after targeted/module/full regression checks:

python tools\import_sar_dark_spot_candidates_v01.py `
  --input validation\gee_sentinel1_dark_spot_candidates_v01.json

Then verify via:
GET /satellite/observations/

Do not create Event links in SAT-8.
