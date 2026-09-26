import test from "node:test";
import assert from "node:assert/strict";

import {
  hasSingleTimelineRoot,
} from "./timelineDomCleanup.js";

test("checks single timeline root", () => {
  assert.equal(
    hasSingleTimelineRoot(
      "<div class='evidence-vertical-timeline'></div>",
    ),
    true,
  );

  assert.equal(
    hasSingleTimelineRoot(
      "<div class='evidence-vertical-timeline'><div class='evidence-vertical-timeline'></div></div>",
    ),
    false,
  );
});
