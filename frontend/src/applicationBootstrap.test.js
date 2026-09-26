import test from "node:test";
import assert from "node:assert/strict";

import {
  bootstrapApplication,
} from "./applicationBootstrap.js";


test("bootstrap switches to map callback", async () => {
  let started = false;

  const result = await bootstrapApplication({
    startMapApplication: async () => {
      started = true;
    },
  });

  assert.equal(result, "map");
  assert.equal(started, true);
});
