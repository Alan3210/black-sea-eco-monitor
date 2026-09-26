import test from "node:test";
import assert from "node:assert/strict";

import {
  buildTimelineEmptyState,
  buildTimelineSourceLink,
} from "./timelineEmptyState.js";

test("handles empty timeline", () => {
  const result = buildTimelineEmptyState([]);
  assert.equal(result.empty, true);
});

test("keeps source metadata", () => {
  const result = buildTimelineSourceLink({
    title: "Observation",
    source: "Sentinel-5P",
  });

  assert.equal(result.source, "Sentinel-5P");
});
