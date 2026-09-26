import test from "node:test";
import assert from "node:assert/strict";

import { normalizeEventTimeline, hasRealTimeline } from "./realEvidenceTimelineBinding.js";

test("normalizes event timeline payload", () => {
  const event = {
    timeline: [
      {
        type: "observation",
        title: "Satellite observation",
        source: "Sentinel-5P",
        time: "01:30",
      },
    ],
  };

  assert.equal(hasRealTimeline(event), true);
  assert.equal(normalizeEventTimeline(event)[0].source, "Sentinel-5P");
});
