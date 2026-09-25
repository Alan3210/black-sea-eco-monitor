import test from "node:test";
import assert from "node:assert/strict";

import { normalizeGroundStation } from "./groundStationApi.js";

test("normalizes station response", () => {
  const result = normalizeGroundStation({
    station_id: "SPO-1",
    station_name: "Test",
    latitude: 42,
    longitude: 27,
    value: 10,
  });

  assert.equal(result.id, "SPO-1");
  assert.equal(result.lat, 42);
  assert.equal(result.lon, 27);
});
