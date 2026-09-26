import test from "node:test";
import assert from "node:assert/strict";

import {
  buildIncidentReport,
  renderIncidentReportPreview,
} from "./incidentReportExport.js";

test("builds incident report", () => {
  const report = buildIncidentReport({
    title: "Utrish Reserve",
    evidence: [{}],
    timeline: [{}, {}],
  });

  assert.equal(report.evidence.length, 1);
  assert.equal(report.timeline.length, 2);
  assert.match(
    renderIncidentReportPreview(report),
    /Incident Report/,
  );
});
