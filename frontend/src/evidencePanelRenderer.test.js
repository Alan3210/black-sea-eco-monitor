import test from "node:test";
import assert from "node:assert/strict";

import {
  renderEvidencePanel,
} from "./evidencePanelRenderer.js";

test("renders evidence panel blocks", () => {
  const html = renderEvidencePanel({
    sources: [
      {
        name: "EEA",
        available: true,
      },
    ],
    timeline: {
      pollutant: "PM10",
    },
  });

  assert.match(html, /Sources/);
  assert.match(html, /Quality/);
  assert.match(html, /Timeline/);
});
