EkoKontur — SYSTEM-4 Event -> OpenDrift -> Impact Screening v0.1

Purpose
-------
Connect a selected canonical event in the existing Web GIS to the existing
OpenDrift forecast workflow and then to the existing Impact Forecast API.

This block is frontend integration only. It does not add a new backend model,
does not change EventStore schema, and does not start a second drift model.

Operator flow
-------------
1. Select a canonical event on the map.
2. In MODEL WORKFLOW, click "Use event point".
3. The event coordinates become the existing OpenDrift seed.
4. Adjust the existing horizon/particle controls on the left if needed.
5. Run the existing OpenDrift forecast.
6. When that forecast is ready, click "Screen locations · 5 km".
7. The already-produced drift payload is POSTed to /impact/drift.
8. Screening results are shown in the selected event panel and known
   EventStore locations are rendered as map target points.

Semantic guard
--------------
- Canonical event = stored event information.
- OpenDrift result = model forecast.
- Impact result = particle-proximity screening against known EventStore
  locations.
- "Within threshold" does NOT mean confirmed pollution, damage, shoreline
  impact, exposure, or oiling.
- Impact targets in v0.1 are only locations already known to EventStore.
  They are not a complete registry of coastline, settlements, protected
  areas or infrastructure.

Impact API contract used
------------------------
POST /impact/drift

Body:
{
  "forecast": <existing OpenDrift response>,
  "proximity_threshold_km": 5.0
}

The Impact API does not start OpenDrift, OpenOil, Copernicus or ECMWF.

Files added
-----------
frontend/src/impact.js
frontend/src/impact.test.js
tools/install_system4_event_drift_impact_v01.py
README_SYSTEM4_EVENT_DRIFT_IMPACT_V01.txt

Existing files modified by installer
------------------------------------
frontend/src/main.js
frontend/src/i18n.js
frontend/src/style.css
frontend/vite.config.js

Vite proxy
----------
Adds:
/impact -> http://127.0.0.1:8000

Install
-------
From repository root:

python .\tools\install_system4_event_drift_impact_v01.py

Validation
----------
Frontend targeted:
cd frontend
node --test src/impact.test.js

Frontend regression:
npm test

Production build:
npm run build

Backend regression:
cd ..
python -m pytest -q

Runtime smoke
-------------
Backend:
uvicorn backend.main:app --reload

Frontend:
cd frontend
npm run dev

Open:
http://127.0.0.1:5173

Manual checks
-------------
1. Existing events, filters, currents, drift, satellite and context still work.
2. Select an event and verify MODEL WORKFLOW appears.
3. Click "Use event point".
4. Existing OpenDrift seed coordinates update to the event point.
5. Run OpenDrift from the existing controls.
6. Return to the event panel: screening button is enabled.
7. Run screening.
8. Verify summary counts and target rows appear.
9. Verify target markers appear on the map.
10. Verify the disclaimer clearly says this is proximity screening, not
    confirmed impact or pollution.
