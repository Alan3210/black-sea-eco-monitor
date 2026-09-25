import test from "node:test";
import assert from "node:assert/strict";

import {
  renderEvidenceCrosscheckHTML,
} from "./evidenceCrosscheckRenderer.js";

test("renders evidence crosscheck html", () => {
  const html = renderEvidenceCrosscheckHTML({
    title: "Evidence Crosscheck",
    sections: [
      {
        provider: "EEA",
        type: "station_measurement",
        rows: [
          {
            label: "PM10",
            value: "70 ug.m-3",
          },
        ],
      },
    ],
  });

  assert.match(html, /Evidence Crosscheck/);
  assert.match(html, /EEA/);
  assert.match(html, /PM10/);
});
