import test from "node:test";
import assert from "node:assert/strict";

import {
  buildImpactZonesState,
  impactZonesToFeatures,
} from "./impactZonesMap.js";

test("builds impact zones features", () => {
  const state = buildImpactZonesState({
    zones: [
      {
        name: "Reserve A",
        exposureHours: 24,
        geometry: {
          type: "Point",
          coordinates: [37, 44],
        },
      },
    ],
  });

  assert.equal(state.available, true);
  assert.equal(
    impactZonesToFeatures(state).features.length,
    1,
  );
});
