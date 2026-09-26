import test from "node:test";
import assert from "node:assert/strict";

import {
  buildImpactForecastViewModel,
  renderImpactForecastSummary,
} from "./impactForecastResult.js";

test("builds impact forecast view model", () => {
  const vm = buildImpactForecastViewModel({
    affectedAreas: 3,
    closestDistanceKm: 12,
  });

  assert.equal(vm.affectedAreas, 3);
  assert.match(renderImpactForecastSummary(vm), /Impact Forecast/);
});
