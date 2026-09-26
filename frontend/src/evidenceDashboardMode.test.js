import test from "node:test";
import assert from "node:assert/strict";

import {
  isDashboardMode,
} from "./evidenceDashboardMode.js";

test("dashboard mode detection", () => {
  assert.equal(isDashboardMode("#dashboard"), true);
  assert.equal(isDashboardMode("#map"), false);
});
