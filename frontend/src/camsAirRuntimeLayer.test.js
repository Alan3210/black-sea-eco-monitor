import test from "node:test";
import assert from "node:assert/strict";

import {
  createCamsAirRuntimeLayer,
} from "./camsAirRuntimeLayer.js";


test("creates runtime CAMS heatmap layer model", () => {
  const layer =
    createCamsAirRuntimeLayer({
      grid: {
        latitudes: [1],
        longitudes: [2],
        values: [[3]],
      },
    });

  assert.equal(
    layer.source,
    "cams-air-quality"
  );

  assert.equal(
    layer.layer.type,
    "heatmap"
  );

  assert.equal(
    layer.geojson.features.length,
    1
  );
});
