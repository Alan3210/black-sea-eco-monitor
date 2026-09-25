import test from "node:test";
import assert from "node:assert/strict";

import {
  getEvidenceSourceStyle,
  decorateEvidenceSections,
} from "./evidenceCrosscheckStyles.js";

test("returns source style for EEA station", () => {
  const style = getEvidenceSourceStyle(
    "station_measurement",
  );

  assert.equal(style.label, "Ground Station");
});

test("decorates evidence sections", () => {
  const result = decorateEvidenceSections([
    {
      type: "model_forecast",
    },
  ]);

  assert.equal(
    result[0].style.label,
    "Model Forecast",
  );
});
