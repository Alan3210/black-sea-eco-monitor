import test from "node:test";
import assert from "node:assert/strict";

import {
  shouldOpenDashboard,
} from "./evidenceDashboardEntry.js";

test("dashboard hash mode", () => {
  assert.equal(
    shouldOpenDashboard("#dashboard"),
    true,
  );

  assert.equal(
    shouldOpenDashboard("#map"),
    false,
  );
});
