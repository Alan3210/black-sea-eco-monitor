import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEEATimelineSeries,
  normalizeEEATimelinePoints,
} from "./eeaTimelineProvider.js";

test("normalizes EEA timeline series", () => {
  const points = normalizeEEATimelinePoints([
    {
      timestamp: "2026-09-25T10:00:00Z",
      value: 42,
    },
    {
      timestamp: "bad",
      value: null,
    },
  ]);

  assert.equal(points.length, 1);

  const series = buildEEATimelineSeries(points);

  assert.equal(series.source, "EEA");
  assert.equal(series.points.length, 1);
});
