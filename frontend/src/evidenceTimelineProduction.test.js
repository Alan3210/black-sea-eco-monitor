import test from "node:test";
import assert from "assert/strict";

import {
  buildProductionTimelineBlock,
} from "./evidenceTimelineProduction.js";

test("renders production timeline block", () => {
  const html = buildProductionTimelineBlock({
    timeline: [
      {
        type: "observation",
        title: "Satellite observation",
        source: "Sentinel-5P",
      },
    ],
  });

  assert.match(html, /Satellite observation/);
  assert.match(html, /🛰/);
});
