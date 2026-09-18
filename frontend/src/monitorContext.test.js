import test from 'node:test';
import assert from 'node:assert/strict';

import {
  monitorContextViewModel,
} from './monitorContext.js';

test('monitor context view model exposes readiness', () => {
  const vm = monitorContextViewModel({
    satellite: { count: 3 },
    readiness: {
      event_has_coordinates: true,
    },
    capabilities: {
      ocean_drift: { available: true },
      impact_screening: { available: true },
      ar_scene: { available: true },
    },
  });

  assert.equal(vm.satelliteCount, 3);
  assert.equal(vm.hasCoordinates, true);
  assert.equal(vm.driftReady, true);
  assert.equal(vm.impactReady, true);
  assert.equal(vm.arReady, true);
});

test('monitor context view model defaults safely', () => {
  const vm = monitorContextViewModel(null);

  assert.deepEqual(vm, {
    satelliteCount: 0,
    hasCoordinates: false,
    driftReady: false,
    impactReady: false,
    arReady: false,
  });
});
