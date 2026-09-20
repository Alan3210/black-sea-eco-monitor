import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCamsAirCellGeoJSON,
  camsAxisEdges,
  camsFieldStops,
  camsFieldViewModel,
  camsFillColorExpression,
  camsPercentile,
  camsRobustFieldStops,
  normalizeCamsOpacityPercent,
} from "./camsAirOperationalField.js";


test("builds CAMS concentration cells from canonical grid", () => {
  const result =
    buildCamsAirCellGeoJSON({
      grid: {
        latitudes: [1, 2],
        longitudes: [10, 11],
        values: [
          [5, 6],
          [7, 8],
        ],
      },
    });

  assert.equal(result.features.length, 4);
  assert.equal(result.features[0].geometry.type, "Polygon");
  assert.equal(result.features[0].properties.value, 5);
});


test("creates coordinate cell edges", () => {
  assert.deepEqual(
    camsAxisEdges([1, 2]),
    [0.5, 1.5, 2.5],
  );
});


test("creates concentration-driven fallback color stops", () => {
  assert.deepEqual(
    camsFieldStops({
      min: 10,
      max: 30,
    }),
    [10, 15, 20, 25, 30],
  );

  const expression =
    camsFillColorExpression({
      statistics: {
        min: 10,
        max: 30,
      },
    });

  assert.equal(
    expression[0],
    "interpolate",
  );
});


test("normalizes CAMS field opacity", () => {
  assert.equal(
    normalizeCamsOpacityPercent(5),
    20,
  );

  assert.equal(
    normalizeCamsOpacityPercent(120),
    90,
  );

  assert.equal(
    normalizeCamsOpacityPercent("60"),
    60,
  );
});


test("uses 55 percent when localStorage value is missing", () => {
  assert.equal(
    normalizeCamsOpacityPercent(null),
    55,
  );

  assert.equal(
    normalizeCamsOpacityPercent(undefined),
    55,
  );

  assert.equal(
    normalizeCamsOpacityPercent(""),
    55,
  );
});


test("calculates interpolated percentiles", () => {
  assert.equal(
    camsPercentile(
      [0, 10, 20, 30, 40],
      0.5,
    ),
    20,
  );

  assert.equal(
    camsPercentile(
      [0, 10, 20, 30, 40],
      0.25,
    ),
    10,
  );
});


test("robust CAMS stops suppress an extreme maximum", () => {
  const payload = {
    grid: {
      values: [
        [1, 2, 3, 4, 5],
        [6, 7, 8, 9, 1000],
      ],
    },
    statistics: {
      min: 1,
      max: 1000,
    },
  };

  const stops =
    camsRobustFieldStops(
      payload,
    );

  assert.equal(
    stops.length,
    5,
  );

  assert.ok(
    stops[4] < 1000,
  );

  assert.ok(
    stops[2] < 10,
  );
});


test("builds CAMS operational view model", () => {
  const vm =
    camsFieldViewModel({
      pollutant: {
        id: "pm25",
        label: "PM2.5",
        units: "µg/m3",
      },
      model: "ensemble",
      run_time:
        "2026-09-19T00:00:00+00:00",
      valid_time:
        "2026-09-19T06:00:00+00:00",
      lead_hour: 6,
      statistics: {
        min: 3,
        mean: 8,
        max: 27,
      },
      grid: {
        values: [
          [3, 5, 7],
          [8, 9, 27],
        ],
      },
    });

  assert.equal(vm.pollutant, "PM2.5");
  assert.equal(vm.minimum, 3);
  assert.equal(vm.mean, 8);
  assert.equal(vm.maximum, 27);
  assert.equal(vm.leadHour, 6);

  assert.ok(
    vm.legendMax <= 27,
  );
});


test("robust field falls back when too few finite values exist", () => {
  assert.deepEqual(
    camsRobustFieldStops({
      grid: {
        values: [[5, null]],
      },
      statistics: {
        min: 5,
        max: 25,
      },
    }),
    [5, 10, 15, 20, 25],
  );
});
