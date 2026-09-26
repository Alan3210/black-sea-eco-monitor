import test from "node:test";
import assert from "node:assert/strict";

import {
  normalizeTimelinePayload,
  createTimelinePoint,
} from "./timelineDataContract.js";

test("normalizes timeline contract", () => {
  const point = createTimelinePoint(
    "2026-09-25T10:00:00Z",
    42,
  );

  assert.equal(point.value, 42);

  const result = normalizeTimelinePayload({
    pollutant: "PM10",
    series: [
      {
        source: "EEA",
        points: [point],
      },
    ],
  });

  assert.equal(result.series.length, 3);
  assert.equal(result.series[0].points.length, 1);
});
