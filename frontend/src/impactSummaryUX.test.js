import test from "node:test";
import assert from "node:assert/strict";

import {
  buildImpactSummaryState,
  renderImpactSummaryUX,
} from "./impactSummaryUX.js";

test("renders impact summary UX", () => {
  const state = buildImpactSummaryState({
    affectedAreas: 3,
    closestDistanceKm: 12,
    firstExposureHours: 18,
  });

  assert.equal(state.affectedAreas, 3);
  assert.match(
    renderImpactSummaryUX(state),
    /Impact Forecast/,
  );
});
