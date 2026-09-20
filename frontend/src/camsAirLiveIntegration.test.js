
import test from "node:test";
import assert from "node:assert/strict";

import {
  CAMS_RUNTIME_CONFIG,
  buildCamsRequestParams,
} from "./camsAirLiveIntegration.js";

test("defines live CAMS runtime endpoint", () => {
  assert.equal(
    CAMS_RUNTIME_CONFIG.endpoint,
    "/air/field"
  );
});

test("builds CAMS query parameters", () => {
  const params =
    buildCamsRequestParams({
      pollutant: "pm25",
      stride: 2,
    });

  assert.equal(
    params.get("pollutant"),
    "pm25"
  );
});
