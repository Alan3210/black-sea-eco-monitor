import test from "node:test";
import assert from "node:assert/strict";

import {
  selectEvidenceEvent,
  buildEvidencePanelRequest,
} from "./evidencePanelBinding.js";

test("binds event to evidence panel", () => {
  const state = {
    visible: false,
    selectedEventId: null,
  };

  const next = selectEvidenceEvent(
    state,
    "event-1",
  );

  assert.equal(next.visible, true);
  assert.equal(next.selectedEventId, "event-1");

  const request = buildEvidencePanelRequest(
    "event-1",
  );

  assert.equal(
    request.endpoint,
    "/air/evidence-crosscheck",
  );
});
