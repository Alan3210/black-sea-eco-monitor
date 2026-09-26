import test from "node:test";
import assert from "node:assert/strict";

import {
  renderEvidenceTimeline,
} from "./evidenceTimelineRenderer.js";

test("renders visual evidence timeline", () => {
  const html = renderEvidenceTimeline([
    {
      type: "observation",
      title: "Satellite observation",
      source: "Sentinel-5P",
      time: "01:30",
    },
  ]);

  assert.match(html, /Satellite observation/);
  assert.match(html, /🛰/);
});
