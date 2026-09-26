import test from "node:test";
import assert from "node:assert/strict";

import {
  composeEvidencePanelContent,
} from "./evidencePanelContentComposer.js";

test("preserves timeline in panel content", () => {
  const html = composeEvidencePanelContent(
    { id: "event-1" },
    "<div class='evidence-vertical-timeline'>Timeline</div>",
  );

  assert.match(html, /Evidence Event/);
  assert.match(html, /evidence-vertical-timeline/);
});
