SYSTEM-4.2 Persistent Model Scenario v0.1

Fixes the UI architecture where a valid manual/SAR OpenDrift scenario was
hidden whenever no Event was selected.

After installation:
- manual sea-point selection opens the right-side model workflow by itself;
- completed manual/SAR forecasts can run "Screen locations · 5 km";
- Event selection is optional for model scenarios;
- closing an Event falls back to the active standalone scenario;
- Impact loading/error/results belong to the current model scenario;
- clearing the drift scenario closes the standalone panel when nothing else
  is selected.

No backend changes.

Install from repository root:
python .\tools\install_system4_2_persistent_model_scenario_v01.py

Then:
cd .\frontend
npm test

Expected after SYSTEM-4.1: 73 tests, 0 failed.
