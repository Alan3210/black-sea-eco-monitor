import test from "node:test";
import assert from "node:assert/strict";

import {
  buildShareIncidentSummary,
  renderShareSummary,
} from "./shareIncidentSummary.js";

test("builds share incident summary", () => {
  const summary = buildShareIncidentSummary({
    title: "Utrish Reserve",
    evidence: [{}],
    timeline: [{}, {}],
  });

  assert.equal(summary.evidenceCount, 1);
  assert.match(
    renderShareSummary(summary),
    /Incident Summary/,
  );
});
