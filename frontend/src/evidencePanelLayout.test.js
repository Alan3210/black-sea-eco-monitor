import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidencePanelLayout,
} from "./evidencePanelLayout.js";

test("builds styled evidence panel layout", () => {
  const result = buildEvidencePanelLayout({
    status: "ready",
  });

  assert.equal(result.cards.length, 4);
  assert.equal(result.cards[0].type, "sources");
  assert.equal(result.statusClass, "evidence-status-ready");
});
