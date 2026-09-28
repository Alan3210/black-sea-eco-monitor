import test from 'node:test';
import assert from 'node:assert/strict';

import {
  normalizeInvestigationPayload,
} from './investigationNormalizer.js';


test(
  'normalizes investigation API payload',
  () => {
    const result =
      normalizeInvestigationPayload({
        event_id: 'evt_123',

        evidence: [
          {
            id: 'ev_1',
            event_id: 'evt_123',

            evidence_type:
              'satellite_observation',

            source:
              'Sentinel-1',

            timestamp:
              '2026-09-28T10:30:00Z',

            confidence:
              0.9,

            location: {
              latitude: '44.72',
              longitude: '37.45',
            },

            metadata: {
              relation_confidence:
                0.75,
            },

            provenance: {
              dataset_id:
                'COPERNICUS/S1_GRD',
            },
          },
        ],

        candidate_sources: [
          {
            type: 'vessel',
            id: 'candidate_1',
          },
        ],
      });

    assert.equal(
      result.eventId,
      'evt_123',
    );

    assert.equal(
      result.evidence.length,
      1,
    );

    assert.equal(
      result.evidence[0].type,
      'satellite_observation',
    );

    assert.deepEqual(
      result.evidence[0].location,
      {
        latitude: 44.72,
        longitude: 37.45,
      },
    );

    assert.equal(
      result.evidence[0].confidence,
      0.9,
    );

    assert.equal(
      result.candidateSources.length,
      1,
    );
  },
);


test(
  'normalizer defaults malformed collections safely',
  () => {
    const result =
      normalizeInvestigationPayload({
        event_id: 'evt_123',
        evidence: null,
        candidate_sources: null,
      });

    assert.deepEqual(
      result,
      {
        eventId: 'evt_123',
        evidence: [],
        candidateSources: [],
      },
    );
  },
);