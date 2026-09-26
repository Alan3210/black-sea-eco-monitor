import test from "node:test";
import assert from "node:assert/strict";

import {
  mountEvidencePanelContent,
} from "./evidencePanelContentMount.js";

test("mounts evidence panel content", () => {
  const panel = {
    style: {},
  };

  const container = {
    innerHTML: "",

    closest(selector) {
      if (selector === "#evidence-panel") {
        return panel;
      }

      return null;
    },
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

  assert.equal(
    panel.style.display,
    "",
  );
});