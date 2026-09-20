import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  buildCrosscheckViewModel,
  buildGeosCfCellCollection,
  formatFieldValue,
  inferEdges,
  robustStops,
} from './geosCfOperationalField.js';

describe('inferEdges', () => {
  it('builds midpoint edges for a regular GEOS-CF grid', () => {
    assert.deepEqual(
      inferEdges([26.0, 26.25, 26.5]),
      [25.875, 26.125, 26.375, 26.625],
    );
  });
});

describe('buildGeosCfCellCollection', () => {
  it('skips null cells and keeps valid zero', () => {
    const collection = buildGeosCfCellCollection({
      longitude: [26.0, 26.25],
      latitude: [39.0, 39.25],
      values: [
        [0, null],
        [5, 10],
      ],
    });

    assert.equal(collection.features.length, 3);
    assert.ok(
      collection.features
        .map((feature) => feature.properties.value)
        .includes(0),
    );
  });
});

describe('robustStops', () => {
  it('uses model field percentiles', () => {
    assert.deepEqual(
      robustStops({
        statistics: {
          p05: 5,
          p25: 7,
          p50: 10,
          p75: 13,
          p95: 20,
        },
      }),
      [5, 7, 10, 13, 20],
    );
  });
});

describe('formatFieldValue', () => {
  it('formats model concentration with units', () => {
    assert.equal(
      formatFieldValue(10.9997, 'µg/m³'),
      '11.00 µg/m³',
    );
  });
});

describe('buildCrosscheckViewModel', () => {
  it('extracts operational cross-check metrics', () => {
    const view = buildCrosscheckViewModel({
      semantics: {
        agreement_classification: 'not_calibrated',
      },
      time_alignment: {
        absolute_gap_minutes: 30,
      },
      spatial_alignment: {
        comparison_coverage_percent: 91.93,
        compared_points: 2415,
      },
      metrics: {
        geos_mean: 11.01,
        cams_mean: 6.46,
        bias_geos_minus_cams: 4.55,
        mae: 4.83,
        rmse: 7.14,
        pearson_r: 0.051,
      },
    });

    assert.equal(view.timeGapMinutes, 30);
    assert.equal(view.coveragePercent, 91.93);
    assert.equal(view.comparedPoints, 2415);
    assert.equal(view.bias, 4.55);
    assert.equal(view.classification, 'not_calibrated');
  });
});
