AIR-CLEAN — Remove OpenAQ v0.1
================================

Decision
--------
OpenAQ is removed from the active architecture because it does not provide
useful station coverage for the target Black Sea region.

Primary AIR roadmap becomes:
  CAMS Europe        PRIMARY field
  NASA GEOS-CF       model cross-check / fallback
  Sentinel-5P        satellite evidence
  EEA / local nets   ground observations where available
  NASA FIRMS         source context
  Russian sources    local observations / inventories where usable

Removed
-------
OpenAQ backend runtime:
- backend/services/openaq_client.py
- backend/cache/air_quality_cache.py
- backend/services/air_quality.py
- backend/api/air_quality.py

OpenAQ backend tests:
- test_air_quality_service.py
- test_air_quality_api.py
- test_air_quality_live_cache.py
- test_air_quality_router_registration.py

FastAPI:
- removes air_quality_router import
- removes app.include_router(air_quality_router)
- therefore /air/quality is intentionally removed

OpenAQ experimental README/installers:
- AIR-1.0
- AIR-1.1
- AIR-1.1 fixes
- AIR-1.1.1 fixes
- AIR-1.2 / AIR-1.2.1 installer/history docs

Preserved
---------
The generic station visualization helpers are kept and made provider-neutral:
- frontend/src/airQuality.js
- frontend/src/airQuality.test.js
- frontend/src/airLayer.js
- frontend/src/airLayer.test.js

They no longer contain an OpenAQ default. Their fallback provenance is:
  Ground observation

These helpers can later be reused by:
- EEA stations
- regional monitoring networks
- Russian/local observations

Important
---------
AIR-CLEAN does NOT add CAMS yet.

The next stage is:
  AIR-1.3A CAMS Europe Provider

Install
-------
Extract ZIP into:
  D:\repository\black-sea-eco-monitor

Then:
  cd D:\repository\black-sea-eco-monitor
  python .\tools\install_air_clean_remove_openaq_v01.py

Validation
----------
Backend:
  pytest

Frontend:
  cd .\frontend
  npm test

Expected frontend test total stays at:
  124

The four AIR-1.2 tests + four AIR-1.2.1 tests remain, but are now provider-neutral.
