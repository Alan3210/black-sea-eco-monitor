import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidenceCrosscheckViewModel,
} from "./evidenceCrosscheckView.js";

test("builds evidence view model", () => {
  const result = buildEvidenceCrosscheckViewModel({
    title: "Evidence Crosscheck",
    sources: [
      {
        provider: "EEA",
        type: "station_measurement",
        pollutant: "PM10",
        value: 70,
        unit: "ug.m-3",
      },
    ],
  });

  assert.equal(result.title, "Evidence Crosscheck");
  assert.equal(result.sections.length, 1);
  assert.equal(result.sections[0].provider, "EEA");
});
