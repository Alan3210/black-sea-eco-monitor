import test from "node:test";
import assert from "node:assert/strict";

import {
  createLiveEvidencePanel,
  setEvidencePanelEvent,
} from "./liveEvidencePanel.js";


test("creates live evidence panel workflow", () => {
  let panel = createLiveEvidencePanel();

  panel = setEvidencePanelEvent(
    panel,
    "event-1",
  );

  assert.equal(
    panel.state.selectedEventId,
    "event-1",
  );
});
