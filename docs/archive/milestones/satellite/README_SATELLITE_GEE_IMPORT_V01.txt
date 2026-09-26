EkoKontur — SAT-5 Cached GEE Sentinel-1 Probe Import v0.1

Purpose
-------
Import one real Sentinel-1 scene from the already verified cached
GEE probe into the canonical SatelliteObservation Store.

This step does NOT call Google Earth Engine and does NOT perform
SAR anomaly detection.

Default input
-------------
validation/gee_sentinel1_probe.json

Default scene
-------------
scene index 0: the newest scene saved in the probe.

Mapping
-------
probe.information_type:
    must be "satellite_observation"

probe.derivation_level:
    -> derivation_level

probe.generated_at:
    -> processing_time

probe.query.dataset_id:
    -> dataset_id

scene.acquisition_time:
    -> acquisition_time

scene.platform_number:
    -> platform

scene.scene_id:
    -> source_image_id

scene.footprint_bounds:
    -> geometry

bbox:
    derived from scene.footprint_bounds
    IMPORTANT: it is NOT copied from the query AOI bbox.

Fixed import semantics
----------------------
observation_type = "sar_scene"
sensor = "Sentinel-1"
review_status = "unreviewed"
confidence = null
processing_method = "gee_sentinel1_probe"
processing_version = probe.probe_version

Probe + scene metadata are preserved inside provenance.

Idempotency
-----------
The importer treats this tuple as the cached-ingestion identity:

(source_image_id, processing_version, observation_type)

Re-running the same import returns the existing observation id and
does not insert a duplicate row.

Files
-----
backend/services/satellite/__init__.py
backend/services/satellite/gee_probe_import.py
tools/import_gee_sentinel1_probe_v01.py
tests/test_gee_sentinel1_probe_import.py
README_SATELLITE_GEE_IMPORT_V01.txt

Install
-------
No existing project file is modified by this package.
Extract the ZIP into the repository root.

Syntax
------
python -m py_compile backend\services\satellite\gee_probe_import.py
python -m py_compile tools\import_gee_sentinel1_probe_v01.py
python -m py_compile tests\test_gee_sentinel1_probe_import.py

Targeted tests
--------------
pytest -q tests\test_gee_sentinel1_probe_import.py *> test-results\sat5_import_v01.txt
Get-Content test-results\sat5_import_v01.txt -Tail 30

Live import into canonical EventStore
-------------------------------------
Do this only AFTER targeted/module/full regression checks:

python tools\import_gee_sentinel1_probe_v01.py `
  --probe validation\gee_sentinel1_probe.json

Then verify through:
GET /satellite/observations/
GET /satellite/observations/{observation_id}
