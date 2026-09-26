import test from "node:test";
import assert from "node:assert/strict";

import { loadEvidenceDashboard } from "./evidenceDashboardController.js";

test("loads dashboard data binding", async () => {
  const mockFetch = async () => ({
    ok: true,
    json: async () => ({
      sources: {},
      series: [],
      quality: {},
    }),
  });

  const result = await loadEvidenceDashboard(mockFetch);

  assert.equal(result.title, "Evidence Dashboard");
});
