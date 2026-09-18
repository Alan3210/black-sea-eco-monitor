EkoKontur — SAT-7A Sentinel-1 VV Calibration Probe v0.1

Purpose:
Measure the real VV backscatter distribution for the already selected
Sentinel-1 scene before choosing a SAT-7B dark-spot threshold.

Semantics:
information_type = satellite_observation
derivation_level = processed
analysis_type = sar_vv_calibration

This is calibration only. It does NOT mean:
oil_spill
confirmed_pollution
confirmed_event

Earth Engine inputs:
Sentinel-1: COPERNICUS/S1_GRD, VV in dB
Water mask: ESA/WorldCover/v200, band Map, class 80
Edge-noise guard: VV > -30 dB

Outputs:
p01, p05, p10, p25, p50
valid water pixel count and area
candidate area for -18, -20, -22, -24, -26, -28 dB

Default output:
validation/gee_sentinel1_vv_calibration_v01.json

Install:
Extract into repository root. No existing source file is modified.

Syntax:
python -m py_compile tools\gee_sentinel1_vv_calibration_v01.py
python -m py_compile tests\test_gee_sentinel1_vv_calibration_v01.py

Targeted tests:
python -m pytest -q tests\test_gee_sentinel1_vv_calibration_v01.py *> test-results\sat7a_targeted.txt
Get-Content test-results\sat7a_targeted.txt -Tail 30

Live:
python tools\gee_sentinel1_vv_calibration_v01.py `
  --probe validation\gee_sentinel1_probe.json

If authentication is required, add --authenticate.

Do not select the SAT-7B threshold until the real calibration JSON is reviewed.
