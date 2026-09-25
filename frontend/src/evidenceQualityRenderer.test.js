import test from "node:test";
import assert from "node:assert/strict";

import {
  renderEvidenceQualityHTML,
} from "./evidenceQualityRenderer.js";

test("renders quality html block", () => {
  const html = renderEvidenceQualityHTML({
    freshness: "60s",
    temporal: "exact",
    spatial: "station_point",
    flags: [],
  });

  assert.match(html, /Data Quality/);
  assert.match(html, /60s/);
  assert.match(html, /station_point/);
});
