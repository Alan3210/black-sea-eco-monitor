import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidenceQualityPanel,
} from "./evidenceCrosscheckQualityPanel.js";

test("adds quality block to evidence source", () => {
  const result = buildEvidenceQualityPanel([
    {
      provider: "EEA",
      source_type: "station_measurement",
      quality: {
        freshness_seconds: 60,
        temporal_alignment: "exact",
        spatial_alignment: "station_point",
        quality_flags: [],
      },
    },
  ]);

  assert.equal(result[0].provider, "EEA");
  assert.equal(result[0].quality.freshness, "60s");
  assert.equal(result[0].quality.spatial, "station_point");
});
