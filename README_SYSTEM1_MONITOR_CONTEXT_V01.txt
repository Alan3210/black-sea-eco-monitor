EkoKontur — SYSTEM-1 Monitoring Integration v0.1

Purpose
-------
Add one fast, read-only unified context endpoint around the canonical
EventStore event.

New endpoint
------------
GET /monitor/events/{event_id}/context

Response includes
-----------------
event
evidence
linked satellite observations
event coordinate readiness
capability metadata
canonical API links

Capabilities
------------
Ocean currents:
GET /ocean/currents/

Ocean drift:
GET /ocean/drift/?lon=<event lon>&lat=<event lat>

The context endpoint does NOT run OceanDrift. It only exposes a ready-to-use
link when event coordinates are available.

Impact screening:
POST /impact/drift
targets:
GET /impact/targets

Impact screening expects an already produced drift forecast payload. It does
not start OpenDrift, OpenOil, Copernicus or ECMWF itself.

AR:
GET /api/ar/scene

AR observer coordinates are the user's/device position, not the event
coordinates.

Satellite
---------
Existing linked observations:
GET /monitor/events/{event_id}/satellite-observations

Candidate GeoJSON:
GET /satellite/observations/candidates.geojson

Semantics
---------
SYSTEM-1 is an orchestration/read-side endpoint only.

It does NOT:
- run OceanDrift;
- run Impact analysis;
- call Copernicus;
- call Google Earth Engine;
- update EventStore;
- change database schema;
- create environmental conclusions.

Files
-----
backend/services/monitor_context.py
tools/install_system1_monitor_context_v01.py
tests/test_monitor_event_context_api.py
README_SYSTEM1_MONITOR_CONTEXT_V01.txt

Install
-------
1. Confirm git status is clean.
2. Extract ZIP into repository root.
3. Run:
   python tools\install_system1_monitor_context_v01.py

Syntax
------
python -m py_compile backend\services\monitor_context.py
python -m py_compile backend\api\monitor_events.py
python -m py_compile tests\test_monitor_event_context_api.py

Targeted tests
--------------
python -m pytest -q tests\test_monitor_event_context_api.py *> test-results\system1_targeted.txt
Get-Content test-results\system1_targeted.txt -Tail 30

Live smoke test
---------------
GET /monitor/events/{real_event_id}/context
