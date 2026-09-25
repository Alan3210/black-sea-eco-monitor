import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidenceCrosscheckPanelModel,
} from "./evidenceCrosscheckPanel.js";

test("builds evidence panel model", () => {
  const result = buildEvidenceCrosscheckPanelModel({
    sources: [
      {
        provider: "EEA",
        source_type: "station_measurement",
        pollutant: "NO2",
        value: 10,
        unit: "ug.m-3",
      },
      {
        provider: "CAMS",
        source_type: "model_forecast",
        pollutant: "NO2",
        value: 11,
        unit: "ug.m-3",
      },
    ],
  });

  assert.equal(result.title, "Evidence Crosscheck");
  assert.equal(result.sources.length, 2);
  assert.equal(result.pollutants[0], "NO2");
});
