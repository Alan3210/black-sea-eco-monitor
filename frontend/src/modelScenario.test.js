import test from 'node:test';
import assert from 'node:assert/strict';

import {
  eventCanSeedMarineModel,
  satelliteCandidateSeed,
  seedStatusKey,
  modelScenarioShouldPersist,
} from './modelScenario.js';


test('land fire event is not eligible as a marine model seed', () => {
  assert.equal(
    eventCanSeedMarineModel({
      category: 'industrial_fire',
      locationType: 'city',
      latitude: 44.7,
      longitude: 37.7,
    }),
    false,
  );
});


test('marine pollution in a water body can seed the marine model', () => {
  assert.equal(
    eventCanSeedMarineModel({
      category: 'oil_spill',
      locationType: 'water_body',
      latitude: 44.7,
      longitude: 37.7,
    }),
    true,
  );
});


test('satellite candidate seed uses the mean polygon coordinate', () => {
  const seed = satelliteCandidateSeed({
    id: 'satobs_1',
    properties: {
      candidate_id: 'sar_ds_001',
    },
    geometry: {
      type: 'Polygon',
      coordinates: [[
        [37.0, 44.0],
        [39.0, 44.0],
        [39.0, 46.0],
        [37.0, 46.0],
      ]],
    },
  });

  assert.equal(seed.sourceKind, 'sar_candidate');
  assert.equal(seed.sourceId, 'sar_ds_001');
  assert.equal(seed.longitude, 38.0);
  assert.equal(seed.latitude, 45.0);
});


test('seed status keys distinguish provenance', () => {
  assert.equal(
    seedStatusKey('manual'),
    'workflow.preparedManual',
  );
  assert.equal(
    seedStatusKey(
      'sar_candidate',
      { forecastReady: true },
    ),
    'workflow.forecastReadySar',
  );
});

test('persistent model scenario is hidden with no model state', () => {
  assert.equal(modelScenarioShouldPersist(), false);
});

test('persistent model scenario is visible for a selected seed', () => {
  assert.equal(
    modelScenarioShouldPersist({ seedAvailable: true }),
    true,
  );
});

test('persistent model scenario is visible for a completed forecast', () => {
  assert.equal(
    modelScenarioShouldPersist({ forecastAvailable: true }),
    true,
  );
});

test('persistent model scenario remains visible for impact state', () => {
  assert.equal(
    modelScenarioShouldPersist({ impactError: true }),
    true,
  );
});

