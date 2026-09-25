import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidenceTimelineChartModel,
} from "./evidenceTimelineChartModel.js";

test("builds chart model", () => {
  const result = buildEvidenceTimelineChartModel({
    title: "PM10 Timeline",
    pollutant: "PM10",
    series: [
      {
        label: "EEA",
        type: "station_measurement",
        points: [
          { time: "10:00", value: 20 },
        ],
      },
    ],
  });

  assert.equal(result.axes.x, "time");
  assert.equal(result.axes.y, "value");
  assert.equal(result.pointCount, 1);
});
