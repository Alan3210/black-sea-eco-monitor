import test from "node:test";
import assert from "node:assert/strict";

import {
  buildDataSourceInventory,
  groupDataSourcesByType,
} from "./dataSourceInventory.js";

test("builds data source inventory", () => {
  const inventory = buildDataSourceInventory([
    {
      name: "Sentinel-5P",
      type: "satellite",
      purpose: "Observation",
    },
    {
      name: "CAMS",
      type: "model",
      purpose: "Forecast",
    },
  ]);

  assert.equal(inventory.length, 2);
  assert.equal(
    groupDataSourcesByType(inventory).satellite.length,
    1,
  );
});
