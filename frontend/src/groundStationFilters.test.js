import test from "node:test";
import assert from "node:assert/strict";

import {
  filterGroundStations,
} from "./groundStationFilters.js";

test("filters stations by pollutant and source", () => {
  const result = filterGroundStations([
    {
      pollutant: "PM10",
      source: "EEA",
    },
    {
      pollutant: "NO2",
      source: "OTHER",
    },
  ]);

  assert.equal(result.length, 1);
  assert.equal(result[0].pollutant, "PM10");
});

test("keeps station without timestamp", () => {
  const result = filterGroundStations([
    {
      pollutant: "PM10",
      source: "EEA",
    },
  ]);

  assert.equal(result.length, 1);
});
