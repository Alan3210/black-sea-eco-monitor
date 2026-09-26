import test from "node:test";
import assert from "node:assert/strict";

import {
  createImpactZoneSelection,
  renderImpactZoneDetails,
} from "./impactZoneInteraction.js";

test("creates impact zone selection", () => {
  const zone = createImpactZoneSelection({
    name: "Reserve A",
    distanceKm: 12,
    exposureHours: 24,
  });

  assert.equal(zone.name, "Reserve A");
  assert.match(renderImpactZoneDetails(zone), /Impact Zone/);
});
