import test from "node:test";
import assert from "node:assert/strict";

import {
  mountEvidencePanel,
} from "./evidencePanelMount.js";

test("mounts evidence panel shell", () => {
  const container = {
    innerHTML: "",
  };

  const result = mountEvidencePanel(container);

  assert.equal(result, true);

  assert.match(
    container.innerHTML,
    /id="evidence-panel"/
  );

  assert.match(
    container.innerHTML,
    /id="evidence-panel-content"/
  );

  assert.match(
    container.innerHTML,
    /evidence-panel/
  );
});