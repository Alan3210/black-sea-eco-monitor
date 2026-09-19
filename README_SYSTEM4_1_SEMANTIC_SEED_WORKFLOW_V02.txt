SYSTEM-4.1 Semantic Seed Workflow v0.2

Purpose
-------
Fix the semantic mistake of treating every canonical event coordinate as a
valid OpenDrift seed.

Rules
-----
1. Event point:
   Only marine incident categories with water_body/coastal_area location
   metadata may be used as an event-derived OpenDrift seed.

2. Manual point:
   A manually selected marine point can be forecast and impact-screened.
   It is explicitly not treated as a confirmed event.

3. SAR candidate:
   A SAR dark-spot candidate can be used as a model seed.
   The UI explicitly states that a SAR candidate is not confirmed oil
   pollution.

4. Impact Screening:
   Any completed drift forecast may be screened against Impact Registry
   targets. Screening is no longer artificially restricted to forecasts whose
   seed matches the currently selected event.

Files
-----
frontend/src/modelScenario.js
frontend/src/modelScenario.test.js
tools/install_system4_1_semantic_seed_workflow_v02.py

Installer modifies:
frontend/src/main.js
frontend/src/i18n.js

No backend model or EventStore schema changes are introduced.
