import test from "node:test";
import assert from "node:assert/strict";

import {
  normalizeEvidenceCrosscheck,
} from "./evidenceCrosscheckApi.js";

test("normalizes evidence crosscheck payload", () => {
  const result = normalizeEvidenceCrosscheck({
    sources: [
      {
        provider: "EEA",
        source_type: "station_measurement",
      },
    ],
  });

  assert.equal(result.sources.length, 1);
  assert.equal(result.sources[0].provider, "EEA");
});
