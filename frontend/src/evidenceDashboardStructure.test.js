import test from "node:test";
import assert from "node:assert/strict";

import {
  buildDashboardStructure,
} from "./evidenceDashboardStructure.js";

test("builds dashboard cards", () => {
  const result = buildDashboardStructure({
    title: "Evidence Dashboard",
  });

  assert.equal(result.cards.length, 4);
  assert.equal(result.cards[0].id, "sources");
  assert.equal(result.cards[2].id, "timeline");
});
