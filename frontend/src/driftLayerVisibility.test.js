import test from "node:test";
import assert from "node:assert/strict";

import {
  buildDriftVisualizationState,
  shouldShowDriftLayer,
} from "./driftLayerVisibility.js";

test("builds drift visualization state", () => {
  const state = buildDriftVisualizationState({
    visible: true,
    envelope: {},
  });

  assert.equal(state.available, true);
  assert.equal(shouldShowDriftLayer(state), true);
});

test("hides empty drift layer", () => {
  assert.equal(
    shouldShowDriftLayer(
      buildDriftVisualizationState({}),
    ),
    false,
  );
});
