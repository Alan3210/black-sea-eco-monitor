import test from "node:test";
import assert from "node:assert/strict";

import {
  renderEvidenceDashboardHTML,
} from "./evidenceDashboardRenderer.js";

test("renders dashboard html", () => {
  const html = renderEvidenceDashboardHTML({
    title: "Evidence Dashboard",
    summary: {
      sources: {},
    },
  });

  assert.match(html, /Evidence Dashboard/);
  assert.match(html, /Sources Status/);
  assert.match(html, /Quality Overview/);
});
