EkoKontur — SAT-6 Event ↔ Satellite read side v0.1

Scope
-----
Adds read-only access to already existing event-to-satellite links.

EventStore:
    get_event_satellite_observations(event_id)

API:
    GET /monitor/events/{event_id}/satellite-observations

Response shape
--------------
[
  {
    "relation_type": "spatial_overlap",
    "relation_confidence": null,
    "created_at": "...",
    "observation": {
      "id": "satobs_...",
      "information_type": "satellite_observation",
      "observation_type": "sar_scene",
      "sensor": "Sentinel-1",
      "dataset_id": "COPERNICUS/S1_GRD",
      ...
    }
  }
]

Semantics
---------
The linkage expresses the stored relation only.

For relation_type="spatial_overlap", it means the event coordinates are
inside the observation footprint. It does NOT mean that satellite data
confirmed the event, detected oil, detected fire, or established causality.

Does NOT add
------------
- POST endpoint for links
- automatic linkage
- spatial matcher
- temporal matcher
- SAR anomaly detection
- event confirmation logic
- GEE calls

Files
-----
tools/install_sat6_event_satellite_read_v01.py
tests/test_event_satellite_read_api.py
README_SAT6_EVENT_SATELLITE_READ_V01.txt

Install
-------
1. Confirm clean tree:
   git status --short

2. Extract ZIP into repository root.

3. Run:
   python tools\install_sat6_event_satellite_read_v01.py

4. Syntax:
   python -m py_compile agents\news_agent\event_store.py
   python -m py_compile backend\api\monitor_events.py
   python -m py_compile tests\test_event_satellite_read_api.py

5. Targeted tests:
   python -m pytest -q tests\test_event_satellite_read_api.py *> test-results\sat6_read_v01.txt
   Get-Content test-results\sat6_read_v01.txt -Tail 30

Do not commit before targeted, module, full-regression, and live API checks.
