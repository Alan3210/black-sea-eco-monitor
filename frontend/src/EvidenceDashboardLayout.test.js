import test from "node:test";
import assert from "node:assert/strict";

import {
  buildDashboardLayoutModel,
} from "./EvidenceDashboardLayout.js";

test("builds dashboard layout", () => {
  const result = buildDashboardLayoutModel({
    title: "Evidence Dashboard",
  });

  assert.equal(result.layout.length, 3);
  assert.equal(result.layout[0].columns[0].component, "SourcesStatus");
  assert.equal(result.layout[1].columns[0].component, "EvidenceTimeline");
});
