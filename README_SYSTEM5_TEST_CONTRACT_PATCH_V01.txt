SYSTEM-5 Test Contract Patch v0.1

Purpose
-------
Update the stale Impact API tests after SYSTEM-5 moved Impact targets from
EventStore-derived locations to the dedicated Impact Registry.

This patch does NOT modify runtime backend or frontend code.

It updates:
- tests/test_impact_api.py

It adds/updates:
- tests/test_impact_registry_api.py

Validated contract:
- GET /impact/targets returns 25 registry targets.
- POST /impact/drift screens the supplied forecast against registry targets.
- GET /impact/registry returns registry metadata and 25 targets.

Install from repository root:
python .\tools\install_system5_test_contract_patch_v01.py

Then run:
python -m pytest -q .\tests\test_impact_api.py .\tests\test_impact_service.py .\tests\test_impact_registry_service.py .\tests\test_impact_registry_api.py
