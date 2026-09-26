import test from "node:test";
import assert from "node:assert/strict";

import {
  mountEvidencePanelContent,
} from "./evidencePanelContentMount.js";

test("mounts evidence panel content", () => {
  const container = {
    innerHTML: "",
  };

  const result = mountEvidencePanelContent(
    container,
    {
      sources: [],
    },
  );

  assert.equal(result, true);
  assert.match(
    container.innerHTML,
    /Sources/,
  );
});
