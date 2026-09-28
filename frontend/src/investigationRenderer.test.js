import test from 'node:test';
import assert from 'node:assert/strict';

import {
  renderInvestigationBlock,
} from './investigationRenderer.js';


test(
  'renders canonical investigation evidence',
  () => {
    const html =
      renderInvestigationBlock(
        {
          evidenceCount: 2,

          candidateSourceCount: 0,

          evidence: [
            {
              id: 'source_1',
              type: 'source_report',
              source: 'Test Source',
              title: 'Oil spill report',
              confidence: 0.8,
            },

            {
              id: 'sat_1',
              type:
                'satellite_observation',
              source: 'Sentinel-1',
              confidence: 0.9,

              provenance: {
                dataset_id:
                  'COPERNICUS/S1_GRD',
              },
            },
          ],
        },
        'en',
      );

    assert.match(
      html,
      /Test Source/,
    );

    assert.match(
      html,
      /Sentinel-1/,
    );

    assert.match(
      html,
      /80%/,
    );

    assert.match(
      html,
      /90%/,
    );

    assert.match(
      html,
      /COPERNICUS\/S1_GRD/,
    );
  },
);


test(
  'renders empty investigation state',
  () => {
    const html =
      renderInvestigationBlock(
        {
          evidence: [],
          evidenceCount: 0,
        },
        'en',
      );

    assert.match(
      html,
      /No investigation evidence/,
    );
  },
);