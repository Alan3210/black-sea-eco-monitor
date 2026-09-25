import test from "node:test";
import assert from "node:assert/strict";
import { formatGroundStationObservation, buildGroundStationPopupHTML } from "./groundStationPopup.js";

test("formats station evidence", () => {
  const x = formatGroundStationObservation({station_name:"Test", pollutant:"PM10"});
  assert.equal(x.title, "Test");
});

test("builds html", () => {
  assert.match(buildGroundStationPopupHTML({station_name:"Test"}), /Test/);
});
