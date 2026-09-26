import test from "node:test";
import assert from "node:assert/strict";

import {
  createReportPreviewState,
  renderReportPreview,
} from "./reportPreviewUX.js";

test("renders report preview", () => {
  const state = createReportPreviewState({
    title: "Utrish Reserve",
    evidence: [{}],
    timeline: [{}, {}],
    impact: {},
  });

  const html = renderReportPreview(state);

  assert.match(html, /Incident Report/);
  assert.match(html, /Utrish Reserve/);
});
