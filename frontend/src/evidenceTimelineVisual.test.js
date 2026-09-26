import test from "node:test";
import assert from "node:assert/strict";

import {
  buildVisualTimeline,
} from "./evidenceTimelineVisual.js";

test("builds visual evidence timeline", () => {
  const result = buildVisualTimeline([
    {
      type: "observation",
      title: "Satellite observation",
    },
    {
      type: "model",
      title: "CAMS forecast",
    },
  ]);

  assert.equal(result[0].icon, "🛰");
  assert.equal(result[1].icon, "🌍");
});
