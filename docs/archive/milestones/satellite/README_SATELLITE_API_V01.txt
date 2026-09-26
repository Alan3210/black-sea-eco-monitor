EkoKontur — SAT-4 Read-only Satellite API v0.1

Scope
-----
Adds two read-only endpoints:

GET /satellite/observations/
GET /satellite/observations/{observation_id}

Behavior
--------
Collection:
- HTTP 200
- returns EventStore.list_satellite_observations()

Detail:
- HTTP 200 when found
- HTTP 404 with:
  {"detail":"Satellite observation not found"}
  when missing

Architecture
------------
- separate FastAPI APIRouter
- EventStore supplied through FastAPI Depends()
- router wired from backend/main.py
- tests override dependency with temporary EventStore
- no access to canonical database/events.db during targeted tests

Does NOT add
------------
- POST/PUT/PATCH/DELETE
- GEE calls
- bbox filters
- event filters
- pagination
- Pydantic response schemas
- ingestion/upsert logic

Files
-----
backend/api/satellite_observations.py
tests/test_satellite_observations_api.py
tools/install_satellite_api_v01.py
README_SATELLITE_API_V01.txt

Install
-------
1. Confirm clean tree:
   git status --short

2. Extract ZIP into repository root with -Force.

3. Run:
   python tools\install_satellite_api_v01.py

4. Syntax checks:
   python -m py_compile backend\api\satellite_observations.py
   python -m py_compile backend\main.py
   python -m py_compile tests\test_satellite_observations_api.py

5. Targeted tests:
   pytest -q tests\test_satellite_observations_api.py *> test-results\sat4_api_v01.txt
   Get-Content test-results\sat4_api_v01.txt -Tail 30

Do not commit before targeted tests, module regression, full regression,
and live API checks.
