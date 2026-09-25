import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidenceTimelineModel,
} from "./evidenceTimelineModel.js";

test("builds timeline model", () => {
  const result = buildEvidenceTimelineModel({
    pollutant: "PM10",
    series: [
      {
        source: "EEA",
        source_type: "station_measurement",
        points: [],
      },
    ],
  });

  assert.equal(result.pollutant, "PM10");
  assert.equal(result.series.length, 1);
  assert.equal(result.series[0].source, "EEA");
});
