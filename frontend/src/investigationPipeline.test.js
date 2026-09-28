import test from 'node:test';
import assert from 'node:assert/strict';

import {
  loadInvestigationViewModel,
} from './investigationPipeline.js';


test(
  'loads investigation view model through canonical pipeline',
  async () => {
    const calls = [];

    const vm =
      await loadInvestigationViewModel(
        '/monitor/events/evt_123/investigation',

        async (href) => {
          calls.push(href);

          return {
            ok: true,
            status: 200,

            async json() {
              return {
                event_id: 'evt_123',

                evidence: [
                  {
                    id: 'sat_1',

                    event_id:
                      'evt_123',

                    evidence_type:
                      'satellite_observation',

                    source:
                      'Sentinel-1',

                    confidence:
                      0.9,
                  },
                ],

                candidate_sources: [],
              };
            },
          };
        },
      );

    assert.deepEqual(
      calls,
      [
        '/monitor/events/evt_123/investigation',
      ],
    );

    assert.equal(
      vm.eventId,
      'evt_123',
    );

    assert.equal(
      vm.evidenceCount,
      1,
    );

    assert.equal(
      vm.hasEvidence,
      true,
    );

    assert.deepEqual(
      vm.evidenceTypes,
      [
        'satellite_observation',
      ],
    );

    assert.equal(
      vm.evidence[0].source,
      'Sentinel-1',
    );

    assert.equal(
      vm.evidence[0].confidence,
      0.9,
    );
  },
);


test(
  'missing investigation link returns empty view model without fetching',
  async () => {
    let fetched = false;

    const vm =
      await loadInvestigationViewModel(
        null,

        async () => {
          fetched = true;

          throw new Error(
            'fetch must not run',
          );
        },
      );

    assert.equal(
      fetched,
      false,
    );

    assert.deepEqual(
      vm,
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