import test from "node:test";
import assert from "node:assert/strict";

import {
  mountFinalEvidencePanel,
} from "./finalMapEvidenceMount.js";

test("exports final map evidence mount bridge", () => {
  assert.equal(
    typeof mountFinalEvidencePanel,
    "function",
  );
});
