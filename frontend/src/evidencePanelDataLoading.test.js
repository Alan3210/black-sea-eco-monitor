import test from "node:test";
import assert from "node:assert/strict";

import {
  fetchEvidenceForEvent,
} from "./evidencePanelApi.js";

test("loads evidence request contract", async () => {
  const result = await fetchEvidenceForEvent(
    "event-1",
    async () => ({
      ok: true,
      json: async () => ({
        sources: [],
      }),
    }),
  );

  assert.deepEqual(result.sources, []);
});
