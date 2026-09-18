EkoKontur — SYSTEM-2 Operator Dashboard Read Model v0.1

Purpose
-------
Provide one compact read-only event list for an operator dashboard / Web GIS.

New endpoint
------------
GET /monitor/dashboard/events

Optional filters
----------------
status
category
has_coordinates

Response shape
--------------
{
  "count": 4,
  "items": [
    {
      "id": "evt_...",
      "display_label": "Novorossiysk · industrial_fire",
      "primary_title": "...",
      "category": "industrial_fire",
      "status": "detected",
      "severity": "medium",
      "confidence": 0.8,
      "location": {
        "name": "Novorossiysk",
        "latitude": 44.724,
        "longitude": 37.7691,
        "type": "city"
      },
      "event_time": "...",
      "updated_at": "...",
      "evidence_count": 3,
      "satellite_count": 1,
      "readiness": {
        "has_coordinates": true,
        "ocean_drift": true,
        "impact_after_drift": true,
        "ar_scene": true
      },
      "links": {
        "event": "...",
        "context": "...",
        "evidence": "...",
        "satellite_observations": "..."
      }
    }
  ]
}

Notes
-----
primary_title is passed through exactly as stored in canonical EventStore.
SYSTEM-2 does not attempt to repair or reinterpret malformed source encoding.

display_label is a deterministic clean UI fallback built from:
location name + category.

impact_after_drift means workflow readiness only:
if the event has coordinates, the system can run OceanDrift and then pass the
result to Impact screening. SYSTEM-2 itself does not start either model.

Does NOT
--------
- change EventStore;
- add database schema;
- run OceanDrift;
- run Impact;
- call Copernicus;
- call GEE;
- infer environmental risk;
- create a risk score.

Files
-----
backend/api/monitor_dashboard.py
backend/services/operator_dashboard.py
tools/install_system2_operator_dashboard_v01.py
tests/test_operator_dashboard_api.py
README_SYSTEM2_OPERATOR_DASHBOARD_V01.txt

Install
-------
1. Confirm git status is clean.
2. Extract ZIP into repository root.
3. Run:
   python tools\install_system2_operator_dashboard_v01.py

Syntax
------
python -m py_compile backend\api\monitor_dashboard.py
python -m py_compile backend\services\operator_dashboard.py
python -m py_compile backend\main.py
python -m py_compile tests\test_operator_dashboard_api.py

Targeted tests
--------------
python -m pytest -q tests\test_operator_dashboard_api.py *> test-results\system2_targeted.txt
Get-Content test-results\system2_targeted.txt -Tail 30

Live
----
GET /monitor/dashboard/events

Examples:
GET /monitor/dashboard/events?status=detected
GET /monitor/dashboard/events?category=industrial_fire
GET /monitor/dashboard/events?has_coordinates=true
