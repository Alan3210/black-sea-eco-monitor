import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEvidenceDashboardPage,
} from "./EvidenceDashboardPage.js";

test("builds dashboard page", () => {
  const result = buildEvidenceDashboardPage({});

  assert.equal(result.route, "/dashboard/evidence");
  assert.equal(result.layout.layout.length, 3);
});
