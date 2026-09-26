EkoKontur — SYSTEM-3 Web GIS MVP v0.1

Purpose
-------
Extend the existing Vite + MapLibre Web GIS without replacing its current
event, filtering, ocean-current, OpenDrift or co-located-event workflows.

Adds:
1. Unified event context inside the existing event detail panel.
2. A separate Sentinel-1 SAR dark-spot candidate map layer.

New API usage
-------------
GET /monitor/events/{event_id}/context
GET /satellite/observations/candidates.geojson

Vite proxy
----------
Adds /satellite -> http://127.0.0.1:8000.

Semantic guard
--------------
SAR polygons are visually separate from canonical Event markers and are
explicitly presented as candidates, not confirmed pollution.

Files added
-----------
frontend/src/satellite.js
frontend/src/satellite.test.js
frontend/src/monitorContext.js
frontend/src/monitorContext.test.js
tools/install_system3_webgis_v01.py
README_SYSTEM3_WEBGIS_V01.txt

Existing frontend files modified by installer
---------------------------------------------
frontend/src/main.js
frontend/index.html
frontend/src/i18n.js
frontend/src/style.css
frontend/vite.config.js

Install
-------
1. Confirm git status is clean.
2. Extract ZIP into repository root.
3. Run:
   python tools\install_system3_webgis_v01.py

Frontend tests
--------------
cd frontend
npm test

Build
-----
npm run build

Development
-----------
Backend:
uvicorn backend.main:app --reload

Frontend:
cd frontend
npm run dev

Open:
http://127.0.0.1:5173

Manual checks
-------------
1. Existing event markers still render.
2. Existing filters still work.
3. Existing currents and OpenDrift UI remain intact.
4. Open an event: SYSTEM CONTEXT appears in the existing event panel.
5. Enable SAR candidates: candidate polygons appear separately from Events.
6. Click a candidate: popup says it is not confirmed pollution.
7. RU / EN switching updates the new labels.
