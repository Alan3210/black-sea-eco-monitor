import test from "node:test";
import assert from "node:assert/strict";

import {
  buildGroundStationGeoJSON,
  GROUND_STATION_LAYER_CONFIG,
} from "./groundStationLayer.js";

test("builds ground station geojson layer data", () => {
  const result = buildGroundStationGeoJSON([
    {
      id: "S1",
      name: "Station",
      lat: 42,
      lon: 27,
    },
  ]);

  assert.equal(result.type, "FeatureCollection");
  assert.equal(result.features.length, 1);
  assert.equal(GROUND_STATION_LAYER_CONFIG.sourceId, "ground-stations");
});
