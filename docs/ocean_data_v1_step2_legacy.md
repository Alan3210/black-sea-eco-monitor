# Ocean Data v1 — Step 2 (legacy package notes)

```text
Ocean Data v1 — Step 2
========================

This package adds the first real Copernicus Marine current-data backend.

ADD:
  agents/ocean_data/__init__.py
  agents/ocean_data/copernicus_currents.py
  backend/api/ocean_currents.py
  tools/install_ocean_data_v1.py
  tools/check_ocean_currents.py
  tests/test_ocean_currents_provider.py
  tests/test_ocean_currents_api.py

No existing source file is replaced directly.

STEP A — copy the package files into the repository root.

STEP B — dry-run the main.py installer:
  python tools/install_ocean_data_v1.py

Expected:
  DRY RUN
  backend/main.py can be patched safely.
  No files changed.

STEP C — apply the main.py patch:
  python tools/install_ocean_data_v1.py --apply

The installer creates a timestamped backup of backend/main.py first.

STEP D — tests:
  pytest -q *> pytest_ocean_step2.txt
  Get-Content pytest_ocean_step2.txt -Tail 15

Expected total after the previous 121-test checkpoint:
  126 passed

STEP E — one live Copernicus smoke test, saved to file:
  python tools/check_ocean_currents.py *> ocean_currents_live.txt
  Get-Content ocean_currents_live.txt

This request downloads only:
  - uo / vo
  - one hourly time step
  - the shallowest model level (~0.5 m)
  - the Black Sea model domain

API after backend restart:
  GET /ocean/currents/
  GET /ocean/currents/?stride=8
  GET /ocean/currents/?at=2026-09-15T06:00:00Z&stride=8

The endpoint returns a decimated vector grid ready for MapLibre.
Default stride=8 means about one displayed vector every 0.2 degrees.

Cache:
  Default location is outside the repository in the OS temporary directory:
  %TEMP%\black-sea-eco-monitor\ocean-currents

Environment override:
  OCEAN_CURRENTS_CACHE_DIR
```
