import test from "node:test";
import assert from "node:assert/strict";

import {
  renderEvidencePanelTimelineBlock,
  composeEvidencePanelContent,
} from "./evidenceTimelineIntegration.js";

test("integrates evidence timeline into panel content", () => {
  const block = renderEvidencePanelTimelineBlock([
    {
      time: "2026-09-13T01:30:00",
      title: "Satellite observation",
      source: "Sentinel-5P",
    },
  ]);

  assert.match(block, /Satellite observation/);

  const content = composeEvidencePanelContent(
    "<div>Base</div>",
    [],
  );

  assert.match(content, /Base/);
});
