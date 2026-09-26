import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidenceEventTimeline,
  renderEvidenceEventTimeline,
} from "./evidenceEventTimeline.js";

test("builds event evidence timeline", () => {
  const timeline = buildEvidenceEventTimeline([
    {
      time: "2026-09-13T01:30:00",
      title: "Satellite observation",
      source: "Sentinel-5P",
    },
  ]);

  assert.equal(timeline.events.length, 1);
  assert.match(
    renderEvidenceEventTimeline(timeline),
    /Satellite observation/,
  );
});
