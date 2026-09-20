import assert from 'node:assert/strict';
import { describe, it } from 'node:test';

import {
  buildTropomiCellCollection,
  formatSatelliteValue,
  inferEdges,
  productDisplayMeta,
  robustStops,
} from './tropomiOperationalField.js';

describe('inferEdges', () => {
  it('builds midpoint edges for a regular grid', () => {
    assert.deepEqual(inferEdges([10, 12, 14]), [9, 11, 13, 15]);
  });
});

describe('buildTropomiCellCollection', () => {
  it('skips null pixels and preserves negative retrievals', () => {
    const collection = buildTropomiCellCollection({
      longitude: [26.025, 26.075],
      latitude: [39.025, 39.075],
      values: [
        [1e-5, null],
        [-2e-6, 3e-5],
      ],
    });

    assert.equal(collection.features.length, 3);
    assert.ok(
      collection.features
        .map((item) => item.properties.value)
        .includes(-2e-6),
    );
  });
});

describe('robustStops', () => {
  it('uses p05/p25/p50/p75/p95', () => {
    assert.deepEqual(
      robustStops({
        statistics: {
          p05: 1,
          p25: 2,
          p50: 3,
          p75: 4,
          p95: 5,
        },
      }),
      [1, 2, 3, 4, 5],
    );
  });
});

describe('display formatting', () => {
  it('converts mol/m^2 to micromol/m^2 for readability', () => {
    assert.equal(productDisplayMeta('no2', 'mol/m^2').factor, 1e6);
    assert.equal(
      formatSatelliteValue(2.5e-5, 'no2', 'mol/m^2'),
      '25.00 µmol/m²',
    );
  });

  it('keeps ppb unchanged', () => {
    assert.equal(
      formatSatelliteValue(1850, 'ch4', 'ppb'),
      '1850.0 ppb',
    );
  });
});
