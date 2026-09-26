EkoKontur — Satellite MVP Final Block v0.1

Purpose
-------
Close and freeze the Sentinel-1 satellite branch as a conference/demo-ready
MVP.

This block adds:
1. Read-only API filters for SatelliteObservation collection.
2. A GeoJSON endpoint for stored SAR dark-spot candidates.
3. A one-command end-to-end demo runner.
4. Cached/demo mode so the conference demonstration does not depend on live
   Google Earth Engine availability.

API
---
Existing:
GET /satellite/observations/
GET /satellite/observations/{observation_id}

New optional collection filters:
observation_type
derivation_level
source_image_id

Examples:
GET /satellite/observations/?observation_type=sar_dark_spot_candidate
GET /satellite/observations/?derivation_level=derived
GET /satellite/observations/?source_image_id=<Sentinel scene id>

New GeoJSON endpoint:
GET /satellite/observations/candidates.geojson

Optional:
source_image_id=<Sentinel scene id>

The GeoJSON endpoint returns only:
observation_type = sar_dark_spot_candidate
derivation_level = derived

Semantic guard
--------------
SAR dark-spot candidates remain satellite-derived candidate observations.

They do NOT mean:
oil spill
confirmed pollution
confirmed event
causal link to event

Demo runner
-----------
tools/run_satellite_mvp_demo_v01.py

Recommended conference mode:
python tools\run_satellite_mvp_demo_v01.py --mode cached

Cached mode:
- uses the already validated cached Sentinel-1 probe;
- uses the cached VV calibration;
- uses the cached dark-spot extraction;
- regenerates the visual verification map;
- idempotently imports candidates into the SatelliteObservation Store;
- writes validation/satellite_mvp_demo_manifest_v01.json.

For a non-mutating rehearsal:
python tools\run_satellite_mvp_demo_v01.py --mode cached --skip-store

Live mode:
python tools\run_satellite_mvp_demo_v01.py --mode live

Live mode requires GEE_PROJECT_ID or --project and runs:
probe
→ calibration
→ extraction
→ verification
→ store

If Earth Engine requires user authentication:
python tools\run_satellite_mvp_demo_v01.py --mode live --authenticate

Safety/reliability
------------------
Before a store-writing demo run, the runner backs up the selected EventStore
database into dev-snapshots unless --no-backup is supplied.

The import stage is idempotent, so rerunning the cached conference demo does
not duplicate already stored dark-spot candidate observations.

Files
-----
tools/install_satellite_mvp_final_v01.py
tools/run_satellite_mvp_demo_v01.py
tests/test_satellite_mvp_final_api.py
tests/test_satellite_mvp_demo_runner.py
README_SATELLITE_MVP_FINAL_V01.txt

Install
-------
1. Confirm clean tree.
2. Extract package into repository root.
3. Run:
   python tools\install_satellite_mvp_final_v01.py

Syntax
------
python -m py_compile backend\api\satellite_observations.py
python -m py_compile tools\run_satellite_mvp_demo_v01.py
python -m py_compile tests\test_satellite_mvp_final_api.py
python -m py_compile tests\test_satellite_mvp_demo_runner.py

Targeted tests
--------------
python -m pytest -q `
  tests\test_satellite_mvp_final_api.py `
  tests\test_satellite_mvp_demo_runner.py `
  *> test-results\satellite_mvp_final_targeted.txt

Conference smoke test
---------------------
python tools\run_satellite_mvp_demo_v01.py --mode cached

Then open:
validation\sat7c_dark_spot_verification_v01.html

After this block passes targeted tests, module regression, full regression,
API live checks and cached demo smoke test, freeze the Satellite MVP branch.
