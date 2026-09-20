import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCamsAirHeatmapGeoJSON,
} from "./camsAirMapLayer.js";


test("builds CAMS heatmap geojson", () => {
  const result =
    buildCamsAirHeatmapGeoJSON({
      grid: {
        latitudes: [1, 2],
        longitudes: [10, 11],
        values: [
          [5, 6],
          [7, 8],
        ],
      },
    });

  assert.equal(
    result.features.length,
    4
  );

  assert.deepEqual(
    result.features[0]
      .geometry
      .coordinates,
    [10, 1]
  );
});
