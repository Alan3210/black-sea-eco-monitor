import test from "node:test";
import assert from "node:assert/strict";

import {
  createEvidencePanelMountPoint,
} from "./evidencePanelHook.js";

test("creates evidence panel mount point contract", () => {
  assert.equal(
    typeof createEvidencePanelMountPoint,
    "function",
  );
});
