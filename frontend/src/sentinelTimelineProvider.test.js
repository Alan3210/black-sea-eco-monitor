import test from "node:test";
import assert from "node:assert/strict";

import {
  buildSentinelTimelineSeries,
  normalizeSentinelTimelinePoints,
} from "./sentinelTimelineProvider.js";

test("normalizes Sentinel-5P timeline series", () => {
  const points = normalizeSentinelTimelinePoints([
    {
      timestamp: "2026-09-25T10:00:00Z",
      value: 18,
    },
    {
      timestamp: "bad",
      value: "x",
    },
  ]);

  assert.equal(points.length, 1);

  const series = buildSentinelTimelineSeries(points);

  assert.equal(series.source, "Sentinel-5P");
  assert.equal(series.points.length, 1);
});
