import test from "node:test";
import assert from "node:assert/strict";

import {
  createImpactForecastState,
  getImpactForecastButtonLabel,
} from "./impactForecastEntry.js";

test("creates impact forecast entry state", () => {
  const state = createImpactForecastState();

  assert.equal(state.action, "run");
  assert.equal(
    getImpactForecastButtonLabel(state),
    "Run Impact Forecast",
  );
});

test("changes button state after forecast", () => {
  const state = createImpactForecastState({
    available: true,
  });

  assert.equal(state.action, "recalculate");
});
