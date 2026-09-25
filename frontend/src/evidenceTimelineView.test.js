import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidenceTimelineViewModel,
} from "./evidenceTimelineView.js";

test("builds timeline view model", () => {
  const result = buildEvidenceTimelineViewModel({
    pollutant: "PM10",
    series: [
      {
        source: "EEA",
        source_type: "station_measurement",
        points: [
          {
            time: "2026-01-01T10:00:00Z",
            value: 20,
          },
        ],
      },
    ],
  });

  assert.equal(result.pollutant, "PM10");
  assert.equal(result.series.length, 1);
  assert.equal(result.series[0].points[0].value, 20);
});
