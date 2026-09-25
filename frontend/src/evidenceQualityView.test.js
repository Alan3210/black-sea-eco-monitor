import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidenceQualityViewModel,
} from "./evidenceQualityView.js";

test("builds quality view model", () => {
  const result = buildEvidenceQualityViewModel({
    freshness_seconds: 60,
    temporal_alignment: "exact",
    spatial_alignment: "station_point",
    quality_flags: [],
  });

  assert.equal(result.freshness, "60s");
  assert.equal(result.temporalAlignment, "exact");
  assert.equal(result.spatialAlignment, "station_point");
});
