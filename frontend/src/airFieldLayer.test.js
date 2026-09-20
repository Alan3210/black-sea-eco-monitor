import test from "node:test";
import assert from "node:assert/strict";

import {
  airFieldToHeatmapPoints,
  airLegendStops,
} from "./airFieldLayer.js";


test("converts CAMS grid into map points", () => {
  const points =
    airFieldToHeatmapPoints({
      pollutant: {
        id: "pm25",
        units: "µg/m³",
      },
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
    points.length,
    4
  );

  assert.equal(
    points[0].value,
    5
  );
});


test("creates legend model", () => {
  const legend =
    airLegendStops("pm25");

  assert.equal(
    legend.units,
    "µg/m³"
  );

  assert.deepEqual(
    legend.stops,
    [0, 10, 25, 50, 100]
  );
});
