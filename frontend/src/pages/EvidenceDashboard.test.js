import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidenceDashboardPageModel,
} from "./EvidenceDashboard.js";

test("builds dashboard page model", () => {
  const result = buildEvidenceDashboardPageModel({
    summary: {
      ready: true,
    },
  });

  assert.equal(result.title, "Evidence Dashboard");
  assert.equal(result.sections.length, 4);
  assert.equal(result.sections[0].id, "summary");
});
