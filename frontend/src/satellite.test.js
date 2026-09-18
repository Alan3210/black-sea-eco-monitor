import test from 'node:test';
import assert from 'node:assert/strict';

import {
  normalizeSatelliteCandidateFeatureCollection,
  satelliteCandidateViewModel,
} from './satellite.js';

test('normalizes only derived SAR candidate features', () => {
  const payload = normalizeSatelliteCandidateFeatureCollection({
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: { type: 'Polygon', coordinates: [] },
        properties: {
          observation_type: 'sar_dark_spot_candidate',
          derivation_level: 'derived',
        },
      },
      {
        type: 'Feature',
        geometry: { type: 'Polygon', coordinates: [] },
        properties: {
          observation_type: 'sar_scene',
          derivation_level: 'processed',
        },
      },
    ],
  });

  assert.equal(payload.features.length, 1);
});

test('candidate view model keeps candidate metadata', () => {
  const vm = satelliteCandidateViewModel({
    id: 'satobs_1',
    properties: {
      candidate_id: 'sar_ds_001',
      area_km2: 0.013,
      mean_vv_db: -25.8,
      threshold_db: -24,
      review_status: 'unreviewed',
      confidence: null,
    },
  });

  assert.equal(vm.id, 'sar_ds_001');
  assert.equal(vm.areaKm2, 0.013);
  assert.equal(vm.meanVvDb, -25.8);
  assert.equal(vm.thresholdDb, -24);
  assert.equal(vm.reviewStatus, 'unreviewed');
  assert.equal(vm.confidence, null);
});
