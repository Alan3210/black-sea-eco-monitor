import test from 'node:test';
import assert from 'node:assert/strict';

import {
  DEFAULT_IMPACT_THRESHOLD_KM,
  fetchDriftImpact,
  impactAssessmentsToFeatureCollection,
  impactSummaryViewModel,
} from './impact.js';


test('posts an existing drift forecast without starting a new model', async () => {
  const forecast = {
    model: 'OpenDrift OceanDrift',
    horizons: [
      {
        hours: 6,
        points: [[37.7, 44.7]],
      },
    ],
  };

  let request = null;

  const fetchImpl = async (url, options) => {
    request = {
      url,
      options,
    };

    return {
      ok: true,
      async json() {
        return {
          target_count: 1,
          potentially_affected_count: 0,
          proximity_threshold_km: 5,
          assessments: [],
        };
      },
    };
  };

  await fetchDriftImpact(
    forecast,
    { thresholdKm: 7.5 },
    fetchImpl,
  );

  assert.equal(request.url, '/impact/drift');
  assert.equal(request.options.method, 'POST');

  const body = JSON.parse(request.options.body);

  assert.deepEqual(body.forecast, forecast);
  assert.equal(body.proximity_threshold_km, 7.5);
});


test('converts impact assessments to map target points', () => {
  const geojson = impactAssessmentsToFeatureCollection({
    assessments: [
      {
        target: {
          id: 'loc_1',
          name: 'Novorossiysk',
          type: 'city',
          position: {
            latitude: 44.724,
            longitude: 37.7691,
          },
        },
        potentially_affected: true,
        first_exposure_hours: 6,
        minimum_distance_km: 0.2,
        closest_horizon_hours: 6,
      },
    ],
  });

  assert.equal(geojson.features.length, 1);
  assert.deepEqual(
    geojson.features[0].geometry.coordinates,
    [37.7691, 44.724],
  );
  assert.equal(
    geojson.features[0].properties.withinThreshold,
    true,
  );
});


test('skips impact targets without valid coordinates', () => {
  const geojson = impactAssessmentsToFeatureCollection({
    assessments: [
      {
        target: {
          id: 'bad',
          name: 'Bad target',
          position: {
            latitude: null,
            longitude: 37.0,
          },
        },
      },
    ],
  });

  assert.equal(geojson.features.length, 0);
});


test('builds a safe impact summary view model', () => {
  const vm = impactSummaryViewModel({
    target_count: 4,
    potentially_affected_count: 1,
    proximity_threshold_km: 5,
    assessments: [{ target: { name: 'A' } }],
  });

  assert.equal(vm.targetCount, 4);
  assert.equal(vm.withinThresholdCount, 1);
  assert.equal(vm.thresholdKm, 5);
  assert.equal(vm.assessments.length, 1);

  assert.equal(
    impactSummaryViewModel(null).thresholdKm,
    DEFAULT_IMPACT_THRESHOLD_KM,
  );
});
