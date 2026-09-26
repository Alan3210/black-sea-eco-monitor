import test from "node:test";
import assert from "node:assert/strict";

import {
  renderRealEventTimeline,
} from "./realTimelineRenderAdapter.js";

test("renders real event timeline adapter", () => {
  const html = renderRealEventTimeline({
    timeline: [
      {
        type: "observation",
        title: "Satellite observation",
        source: "Sentinel-5P",
      },
    ],
  });

  assert.match(html, /Satellite observation/);
  assert.match(html, /Sentinel-5P/);
});
