import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCAMSTimelineSeries,
  normalizeCAMSTimelinePoints,
} from "./camsTimelineProvider.js";

test("normalizes CAMS timeline series", () => {
  const points = normalizeCAMSTimelinePoints([
    {
      timestamp: "2026-09-25T10:00:00Z",
      value: 45,
    },
    {
      timestamp: null,
      value: 12,
    },
  ]);

  assert.equal(points.length, 1);

  const series = buildCAMSTimelineSeries(points);

  assert.equal(series.source, "CAMS");
  assert.equal(series.points.length, 1);
});
