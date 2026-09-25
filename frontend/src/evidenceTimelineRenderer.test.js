import test from "node:test";
import assert from "node:assert/strict";

import {
  renderEvidenceTimelineHTML,
} from "./evidenceTimelineRenderer.js";

test("renders timeline html", () => {
  const html = renderEvidenceTimelineHTML({
    title: "PM10 Timeline",
    series: [
      {
        label: "EEA",
        type: "station_measurement",
        points: [
          {
            time: "10:00",
            value: 20,
          },
        ],
      },
    ],
  });

  assert.match(html, /PM10 Timeline/);
  assert.match(html, /EEA/);
  assert.match(html, /20/);
});
