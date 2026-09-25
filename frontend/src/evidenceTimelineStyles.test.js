import test from "node:test";
import assert from "node:assert/strict";

import {
  getTimelineSourceStyle,
  decorateTimelineSeries,
} from "./evidenceTimelineStyles.js";

test("returns station timeline style", () => {
  const style = getTimelineSourceStyle(
    "station_measurement",
  );

  assert.equal(style.label, "Ground Station");
});

test("decorates timeline series", () => {
  const result = decorateTimelineSeries([
    {
      type: "model_forecast",
    },
  ]);

  assert.equal(
    result[0].style.label,
    "Model Forecast",
  );
});
