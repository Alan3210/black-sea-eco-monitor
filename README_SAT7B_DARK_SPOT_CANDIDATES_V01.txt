EkoKontur — SAT-7B Sentinel-1 SAR Dark-Spot Candidate Extraction v0.1

Purpose
-------
Extract connected dark-spot candidate polygons from the already selected
Sentinel-1 scene after SAT-7A calibration.

This step is intentionally conservative in semantics.

Output semantics
----------------
information_type = satellite_observation
derivation_level = derived
observation_type = sar_dark_spot_candidate

It does NOT mean:
- oil spill
- confirmed pollution
- confirmed event
- causal link to an event

Default v0.1 algorithm
----------------------
1. Sentinel-1 VV from COPERNICUS/S1_GRD
2. Permanent-water mask:
   ESA/WorldCover/v200
   band Map
   class 80
3. Edge guard:
   VV > -30 dB
4. Dark threshold:
   VV < -24 dB
5. 8-connected components
6. Minimum candidate area:
   0.01 km2 = 1 hectare = 100 pixels at 10 m
7. Polygon vectorization
8. Candidate metadata:
   area_km2
   mean_vv_db
   bbox
   GeoJSON geometry
   review_status = unreviewed
   confidence = null

Why -24 dB
-----------
SAT-7A live calibration for the selected scene found:
p01  ≈ -25.12 dB
p05  ≈ -22.87 dB
p10  ≈ -21.87 dB
p25  ≈ -20.12 dB
p50  ≈ -18.38 dB

The -24 dB threshold produced about 9.9 km2 of raw dark water area out
of about 440.9 km2 of valid water in the AOI. It is a prototype threshold,
not a universal oil-detection threshold.

Inputs
------
validation/gee_sentinel1_probe.json
validation/gee_sentinel1_vv_calibration_v01.json

Default output
--------------
validation/gee_sentinel1_dark_spot_candidates_v01.json

Files
-----
tools/gee_sentinel1_dark_spot_candidates_v01.py
tests/test_gee_sentinel1_dark_spot_candidates_v01.py
README_SAT7B_DARK_SPOT_CANDIDATES_V01.txt

Install
-------
Extract into repository root.
No existing source file is modified.

Syntax
------
python -m py_compile tools\gee_sentinel1_dark_spot_candidates_v01.py
python -m py_compile tests\test_gee_sentinel1_dark_spot_candidates_v01.py

Targeted tests
--------------
python -m pytest -q tests\test_gee_sentinel1_dark_spot_candidates_v01.py *> test-results\sat7b_targeted.txt
Get-Content test-results\sat7b_targeted.txt -Tail 30

Live extraction
---------------
Ensure venv is active and GEE_PROJECT_ID is set.

python tools\gee_sentinel1_dark_spot_candidates_v01.py `
  --probe validation\gee_sentinel1_probe.json `
  --calibration validation\gee_sentinel1_vv_calibration_v01.json

If Earth Engine needs authentication, add --authenticate.

Do not import SAT-7B candidates into EventStore yet.
First review the live output JSON and candidate geometry/count.
