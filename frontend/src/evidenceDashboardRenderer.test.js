import test from "node:test";
import assert from "node:assert/strict";

import {
  renderDashboardComponents,
} from "./evidenceDashboardRenderer.js";

test("renders dashboard components", () => {
  const html = renderDashboardComponents({
    summary: {
      sources: {
        station_measurements: true,
      },
    },
    timeline: {
      pollutant: "PM10",
    },
  });

  assert.match(html, /Sources Status/);
  assert.match(html, /Quality Overview/);
  assert.match(html, /Evidence Timeline/);
});
