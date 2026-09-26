import test from "node:test";
import assert from "node:assert/strict";

import {
  getDashboardCardClass,
  getStatusClass,
} from "./evidenceDashboardStyles.js";

test("creates dashboard style classes", () => {
  assert.equal(
    getDashboardCardClass("timeline"),
    "evidence-card evidence-card--timeline",
  );

  assert.equal(
    getStatusClass(true),
    "status-ready",
  );
});
