import test from "node:test";
import assert from "node:assert/strict";

import {
  getGroundStationFeature,
  buildGroundStationPopupFromFeature,
} from "./groundStationInteraction.js";

test("finds ground station feature", () => {
  const feature = getGroundStationFeature({
    features: [
      {
        layer: {
          id: "ground-station-points",
        },
        properties: {
          station_name: "Test",
        },
      },
    ],
  });

  assert.equal(feature.properties.station_name, "Test");
});

test("builds popup from feature", () => {
  const html = buildGroundStationPopupFromFeature({
    properties: {
      station_name: "Test",
    },
  });

  assert.match(html, /Test/);
});
