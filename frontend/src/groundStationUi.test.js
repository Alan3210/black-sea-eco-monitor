import test from "node:test";
import assert from "node:assert/strict";

import {
  buildGroundStationUiModel,
} from "./groundStationUi.js";

test("builds filtered station ui model", () => {
  const result = buildGroundStationUiModel([
    {
      pollutant: "PM10",
      source: "EEA",
      value: 10,
      unit: "ug.m-3",
    },
    {
      pollutant: "NO2",
      source: "OTHER",
      value: 20,
    },
  ]);

  assert.equal(result.stations.length, 1);
  assert.equal(result.legend.length, 1);
});
