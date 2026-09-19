import test from "node:test";
import assert from "node:assert/strict";

import {
  airStationCircleStyle,
  buildAirPopupData,
  createAirStationSourceData,
} from "./airLayer.js";


test("creates generic air station source data", () => {
  const data =
    createAirStationSourceData({
      stations: [
        {
          id: "1",
          lat: 44,
          lon: 37,
          status: "good",
          source: "EEA",
        },
      ],
    });

  assert.equal(
    data.features.length,
    1
  );

  assert.equal(
    data.features[0].properties.source,
    "EEA"
  );
});


test("creates station style", () => {
  const style =
    airStationCircleStyle({
      properties: {
        status: "poor",
      },
    });

  assert.equal(
    style.radius,
    7
  );

  assert.equal(
    style.color,
    "#ff6b6b"
  );
});


test("creates popup model", () => {
  const popup =
    buildAirPopupData({
      name: "Station",
      pm25: 10,
      source: "Regional network",
    });

  assert.equal(
    popup.title,
    "Station"
  );

  assert.equal(
    popup.pm25,
    10
  );

  assert.equal(
    popup.source,
    "Regional network"
  );
});


test("uses neutral fallback source", () => {
  const popup =
    buildAirPopupData({});

  assert.equal(
    popup.source,
    "Ground observation"
  );
});
