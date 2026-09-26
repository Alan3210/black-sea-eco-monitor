import test from "node:test";
import assert from "node:assert/strict";

import {
  appendEvidenceTimeline,
} from "./evidenceTimelineLiveMount.js";

test("appends timeline into panel content", () => {
  const html = appendEvidenceTimeline(
    "<div>Evidence</div>",
    {
      timeline: [
        {
          type: "observation",
          title: "Satellite observation",
        },
      ],
    },
  );

  assert.match(html, /Evidence/);
  assert.match(html, /Satellite observation/);
});
