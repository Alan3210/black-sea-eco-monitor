import test from "node:test";
import assert from "assert/strict";

import {
  mountEvidenceTimelineToPanel,
} from "./evidenceTimelineFinalHook.js";

test("mounts final timeline hook", () => {
  const container = { innerHTML: "" };

  const result = mountEvidenceTimelineToPanel(
    container,
    {
      timeline: [
        {
          type: "observation",
          title: "Satellite observation",
        },
      ],
    },
  );

  assert.equal(result, true);
  assert.match(
    container.innerHTML,
    /Satellite observation/,
  );
});
