import test from "node:test";
import assert from "node:assert/strict";

import {
  formatGroundStationLegendEntry,
  buildGroundStationLegend,
} from "./groundStationLegend.js";

test("formats station legend entry", () => {
  const result = formatGroundStationLegendEntry({
    pollutant: "PM10",
    unit: "ug.m-3",
    source: "EEA",
  });

  assert.equal(result.label, "PM10");
  assert.equal(result.semantics, "station_measurement");
});

test("builds unique legend entries", () => {
  const result = buildGroundStationLegend([
    { pollutant: "PM10", unit: "ug.m-3" },
    { pollutant: "PM10", unit: "ug.m-3" },
  ]);

  assert.equal(result.length, 1);
});
