import test from "node:test";
import assert from "node:assert/strict";

import {
  buildSourcesCard,
  buildQualityCard,
  buildTimelinePanel,
} from "./evidenceDashboardComponents.js";

test("builds dashboard components", () => {
  const sources = buildSourcesCard({
    sources: {
      station_measurements: {available:true},
      model_forecast: {available:true},
    },
  });

  assert.equal(sources.items.length, 3);

  const quality = buildQualityCard({
    fresh_records: 2,
  });

  assert.equal(quality.fresh, 2);

  const timeline = buildTimelinePanel({
    pollutant: "PM10",
  });

  assert.equal(timeline.pollutant, "PM10");
});
