EkoKontur — SatelliteObservation Store v0.1

Scope:
- add only two canonical EventStore tables;
- add only the agreed indexes;
- add schema-only targeted tests;
- no CRUD;
- no API;
- no GEE calls;
- no PRAGMA foreign_keys behavior change.

Files:
  tools/install_satellite_store_v01.py
  tests/test_satellite_observation_store.py

Usage:

1. Verify clean working tree:
   git status --short

2. Extract ZIP into repository root with -Force.

3. Run:
   python tools\install_satellite_store_v01.py

4. Syntax check:
   python -m py_compile agents\news_agent\event_store.py
   python -m py_compile tests\test_satellite_observation_store.py

5. Targeted tests:
   pytest -q tests\test_satellite_observation_store.py *> test-results\satellite_store_v01.txt
   Get-Content test-results\satellite_store_v01.txt -Tail 30

Do not commit yet. Run targeted tests first.
