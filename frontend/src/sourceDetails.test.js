import test from "node:test";
import assert from "node:assert/strict";

import {
  buildSourceDetails,
  renderSourceDetails,
} from "./sourceDetails.js";

test("builds source details", () => {
  const source = buildSourceDetails({
    name: "Sentinel-5P",
    type: "satellite",
    purpose: "Observation",
    relatedEvidence: 3,
  });

  assert.equal(source.name, "Sentinel-5P");
  assert.match(renderSourceDetails(source), /Source Details/);
});
