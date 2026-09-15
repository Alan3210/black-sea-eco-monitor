
import test from "node:test";
import assert from "node:assert/strict";

import {
  CurrentParticleEngine,
} from "../src/currentParticles.js";

test("particle engine exports class", () => {
  assert.equal(
    typeof CurrentParticleEngine,
    "function",
  );
});
