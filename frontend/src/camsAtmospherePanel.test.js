import test from "node:test";
import assert from "node:assert/strict";

import {
  createAtmospherePanelState,
  toggleAirLayer,
  setAirPollutant,
  shouldShowAirLegend,
} from "./camsAtmospherePanel.js";

test("creates atmosphere defaults", () => {
  const state = createAtmospherePanelState();
  assert.equal(state.windEnabled, true);
  assert.equal(state.airEnabled, false);
});

test("toggles CAMS layer", () => {
  const state = toggleAirLayer(
    createAtmospherePanelState(),
    true
  );
  assert.equal(state.airEnabled, true);
  assert.equal(shouldShowAirLegend(state), true);
});

test("changes pollutant", () => {
  const state = setAirPollutant(
    createAtmospherePanelState(),
    "no2"
  );
  assert.equal(state.pollutant, "no2");
});
