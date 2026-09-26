import test from "node:test";
import assert from "node:assert/strict";

import {
  buildProductionTimelineBlock,
  mountProductionTimeline,
} from "./evidenceTimelineProduction.js";

test("production timeline pipeline exports ownership functions", () => {
  assert.equal(
    typeof buildProductionTimelineBlock,
    "function"
  );

  assert.equal(
    typeof mountProductionTimeline,
    "function"
  );
});


test("production timeline pipeline renders timeline data", () => {
  const html = buildProductionTimelineBlock({
    timeline: [
      {
        type: "observation",
        title: "Satellite observation",
      },
    ],
  });

  assert.match(
    html,
    /Satellite observation/
  );
});


test("production timeline mount handles missing container", () => {
  assert.equal(
    mountProductionTimeline(null, {}),
    false
  );
});