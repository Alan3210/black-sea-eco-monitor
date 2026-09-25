import test from "node:test";
import assert from "node:assert/strict";

import {
  findEvidenceTargetFromFeature,
} from "./evidenceCrosscheckMapIntegration.js";

test("extracts evidence target coordinates", () => {
  const result = findEvidenceTargetFromFeature({
    geometry: {
      coordinates: [27, 42],
    },
  });

  assert.equal(result.latitude, 42);
  assert.equal(result.longitude, 27);
});
