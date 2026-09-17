EkoKontur — SAT-3 SatelliteObservation CRUD v0.1

Scope:
- create_satellite_observation()
- get_satellite_observation()
- list_satellite_observations()
- link_satellite_observation_to_event()

Includes:
- JSON geometry/provenance round-trip;
- UTC datetime normalization;
- confidence validation;
- enum validation;
- bbox validation;
- event/observation existence guards;
- idempotent event link;
- lifecycle timestamp preservation.

Does NOT include:
- FastAPI endpoints;
- GEE calls;
- update/delete;
- bbox search;
- ingestion/upsert;
- PRAGMA foreign_keys changes.

Files:
  tools/install_satellite_crud_v01.py
  tests/test_satellite_observation_crud.py

Usage:

1. Confirm clean tree:
   git status --short

2. Extract ZIP into repo root with -Force.

3. Install:
   python tools\install_satellite_crud_v01.py

4. Syntax:
   python -m py_compile agents\news_agent\event_store.py
   python -m py_compile tests\test_satellite_observation_crud.py

5. Targeted tests:
   pytest -q tests\test_satellite_observation_crud.py *> test-results\satellite_crud_v01.txt
   Get-Content test-results\satellite_crud_v01.txt -Tail 30

Do not commit before targeted tests and regression.
