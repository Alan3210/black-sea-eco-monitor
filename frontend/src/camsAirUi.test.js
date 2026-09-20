import test from "node:test";
import assert from "node:assert/strict";

import {
  buildAirLegend,
  createAirToggleState,
  shouldActivateAirLayer,
} from "./camsAirUi.js";


test("creates CAMS toggle state", () => {
  const state =
    createAirToggleState();

  assert.equal(
    state.enabled,
    false
  );

  assert.equal(
    state.pollutant,
    "pm25"
  );
});


test("creates PM2.5 legend", () => {
  const legend =
    buildAirLegend();

  assert.equal(
    legend.units,
    "µg/m³"
  );

  assert.deepEqual(
    legend.stops,
    [0, 10, 25, 50, 100]
  );
});


test("activates layer only when enabled", () => {
  assert.equal(
    shouldActivateAirLayer({
      enabled: true,
    }),
    true
  );

  assert.equal(
    shouldActivateAirLayer({
      enabled: false,
    }),
    false
  );
});
