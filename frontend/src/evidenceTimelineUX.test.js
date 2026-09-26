import test from "node:test";
import assert from "node:assert/strict";

import {
  buildTimelineCard,
  renderVerticalTimeline,
} from "./evidenceTimelineUX.js";

test("builds timeline UX cards", () => {
  const card = buildTimelineCard({
    type: "observation",
    title: "Satellite observation",
  });

  assert.equal(card.icon, "🛰");

  const html = renderVerticalTimeline([
    {
      type: "model",
      title: "CAMS forecast",
    },
  ]);

  assert.match(html, /CAMS forecast/);
});
