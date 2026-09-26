import test from "node:test";
import assert from "node:assert/strict";

import {
  updateTimelineFromSelectedEvent,
} from "./evidenceTimelineEventBinding.js";

test("binds timeline to selected event", () => {
  const result = updateTimelineFromSelectedEvent(
    "event-1",
    {
      timeline: [
        {
          time: "2026-09-13T01:30:00",
          title: "Satellite observation",
          source: "Sentinel-5P",
        },
      ],
    },
  );

  assert.equal(result.eventId, "event-1");
  assert.equal(result.timeline.events.length, 1);
});
