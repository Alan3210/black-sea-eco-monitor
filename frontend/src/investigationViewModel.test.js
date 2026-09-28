import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildInvestigationViewModel,
} from './investigationViewModel.js';


test(
  'groups canonical evidence by type without merging confidence',
  () => {
    const satellite = {
      id: 'sat_1',
      type:
        'satellite_observation',
      confidence: 0.9,
    };

    const weather = {
      id: 'weather_1',
      type:
        'weather_condition',
      confidence: 0.8,
    };

    const vm =
      buildInvestigationViewModel({
        eventId: 'evt_123',

        evidence: [
          satellite,
          weather,
        ],

        candidateSources: [],
      });

    assert.equal(
      vm.eventId,
      'evt_123',
    );

    assert.equal(
      vm.evidenceCount,
      2,
    );

    assert.equal(
      vm.hasEvidence,
      true,
    );

    assert.deepEqual(
      vm.evidenceTypes,
      [
        'satellite_observation',
        'weather_condition',
      ],
    );

    assert.deepEqual(
      vm.evidenceByType
        .satellite_observation,
      [satellite],
    );

    assert.equal(
      vm.evidenceByType
        .satellite_observation[0]
        .confidence,
      0.9,
    );

    assert.equal(
      vm.candidateSourceCount,
      0,
    );
  },
);


test(
  'view model defaults safely',
  () => {
    assert.deepEqual(
      buildInvestigationViewModel(),
      {
        eventId: null,
        evidence: [],
        evidenceCount: 0,
        evidenceByType: {},
        evidenceTypes: [],
        candidateSources: [],
        candidateSourceCount: 0,
        hasEvidence: false,
      },
    );
  },
);