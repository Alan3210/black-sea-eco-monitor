import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidenceDashboardModel,
} from "./evidenceDashboardModel.js";

test("builds dashboard model", () => {
  const result = buildEvidenceDashboardModel({
    summary: {
      sources: {
        stations: true,
      },
    },
    timeline: {
      pollutant: "PM10",
      series: [],
    },
    quality: {
      records: [],
    },
  });

  assert.equal(result.title, "Evidence Dashboard");
  assert.equal(result.timeline.pollutant, "PM10");
  assert.equal(result.summary.sources.stations, true);
});
