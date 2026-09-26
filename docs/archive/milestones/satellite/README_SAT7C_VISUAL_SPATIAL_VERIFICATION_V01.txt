EkoKontur — SAT-7C Visual/Spatial Verification v0.1

Purpose
-------
Human-review helper for the SAT-7B Sentinel-1 SAR dark-spot candidates.

It generates:
1. A compact JSON verification summary.
2. A browser map using Leaflet + Esri World Imagery / Esri World Street Map tiles.

The map lets you visually inspect the candidate polygons relative to the
coastline, Novorossiysk port area, roads, settlements and other map context.

It also overlays candidate bbox centers and reports the nearest stored
canonical EventStore event by coordinate.

This step is verification only.

It does NOT:
- import candidates into EventStore;
- create or update events;
- link candidates to events;
- classify oil;
- confirm pollution;
- establish causality.

Input
-----
validation/gee_sentinel1_dark_spot_candidates_v01.json

Optional read-only contextual source
------------------------------------
database/events.db

The script opens the database in SQLite read-only mode and only reads event
coordinates. If the DB is unavailable, the map/report still work.

Outputs
-------
validation/sat7c_dark_spot_verification_v01.json
validation/sat7c_dark_spot_verification_v01.html

The HTML uses external Leaflet and Esri map resources. Open it in a
browser with internet access for the basemap.

Files
-----
tools/build_sat7c_verification_map_v01.py
tests/test_sat7c_verification_map_v01.py
README_SAT7C_VISUAL_SPATIAL_VERIFICATION_V01.txt

Install
-------
Extract into the repository root. Existing project source files are not
modified.

Syntax
------
python -m py_compile tools\build_sat7c_verification_map_v01.py
python -m py_compile tests\test_sat7c_verification_map_v01.py

Targeted tests
--------------
python -m pytest -q tests\test_sat7c_verification_map_v01.py *> test-results\sat7c_targeted.txt
Get-Content test-results\sat7c_targeted.txt -Tail 30

Live verification
-----------------
python tools\build_sat7c_verification_map_v01.py

Then open:
validation\sat7c_dark_spot_verification_v01.html

No EventStore write is performed.
