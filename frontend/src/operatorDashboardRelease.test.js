import test from "node:test";
import assert from "node:assert/strict";

import {
  createOperatorDashboardState,
  markMapReady,
  markPanelReady,
  selectOperatorEvent,
  markEvidenceLoaded,
} from "./operatorDashboardRelease.js";

test("operator dashboard lifecycle", () => {
  let state = createOperatorDashboardState();

  state = markMapReady(state);
  state = markPanelReady(state);
  state = selectOperatorEvent(state, "event-1");
  state = markEvidenceLoaded(state);

  assert.equal(state.mapReady, true);
  assert.equal(state.panelReady, true);
  assert.equal(state.selectedEventId, "event-1");
  assert.equal(state.evidenceLoaded, true);
});
