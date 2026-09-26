import test from "node:test";
import assert from "node:assert/strict";

import {
  buildSourceOverview,
  renderSourceOverview,
} from "./sourceOverviewBlock.js";

test("builds source overview block", () => {
  const sources = buildSourceOverview([
    {
      name: "Sentinel-5P",
      type: "satellite",
      purpose: "Observation",
    },
  ]);

  assert.equal(sources.length, 1);
  assert.match(
    renderSourceOverview(sources),
    /Sentinel-5P/,
  );
});
