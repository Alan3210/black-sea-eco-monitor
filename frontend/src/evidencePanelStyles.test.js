import test from "node:test";
import assert from "node:assert/strict";

import {
  getEvidenceCardClass,
  getEvidenceStatusClass,
} from "./evidencePanelStyles.js";

test("creates evidence panel style classes", () => {
  assert.equal(
    getEvidenceCardClass("quality"),
    "evidence-panel-card evidence-panel-card--quality",
  );

  assert.equal(
    getEvidenceStatusClass("ready"),
    "evidence-status-ready",
  );
});
