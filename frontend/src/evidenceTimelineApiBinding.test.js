import test from "node:test";
import assert from "node:assert/strict";

import {
  buildTimelineFromEvidencePayload,
  createEvidenceTimelineRequest,
} from "./evidenceTimelineApiBinding.js";

test("builds timeline from evidence payload", () => {
  const timeline = buildTimelineFromEvidencePayload({
    timeline: [
      {
        time: "2026-09-13T01:30:00",
        title: "Satellite observation",
      },
    ],
  });

  assert.equal(timeline.events.length, 1);

  const request = createEvidenceTimelineRequest(
    "event-1",
  );

  assert.equal(
    request.params.include_timeline,
    true,
  );
});
