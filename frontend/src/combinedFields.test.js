import test from 'node:test';
import assert from 'node:assert/strict';

import {
  combinedFieldTimeDeltaMinutes,
  combinedFieldsViewModel,
  combinedWindMeanSpeedMs,
  normalizeCombinedDisplayMode,
} from './combinedFields.js';


test(
  'combined HUD is hidden unless both layers are enabled',
  () => {
    assert.equal(
      combinedFieldsViewModel({
        currentsEnabled: true,
        windEnabled: false,
      }).visible,
      false,
    );

    assert.equal(
      combinedFieldsViewModel({
        currentsEnabled: false,
        windEnabled: true,
      }).visible,
      false,
    );
  },
);


test(
  'combined HUD becomes visible when both layers are enabled',
  () => {
    const view =
      combinedFieldsViewModel({
        currentsEnabled: true,
        windEnabled: true,
      });

    assert.equal(
      view.visible,
      true,
    );

    assert.equal(
      view.state,
      'loading',
    );
  },
);


test(
  'ready state requires both field payloads',
  () => {
    const view =
      combinedFieldsViewModel({
        currentsEnabled: true,
        windEnabled: true,
        currentsPayload: {
          valid_time:
            '2026-09-19T09:00:00Z',
          source:
            'Copernicus Marine',
        },
        windPayload: {
          valid_time:
            '2026-09-19T09:08:00Z',
        },
      });

    assert.equal(
      view.state,
      'ready',
    );
  },
);


test(
  'error state takes precedence over loading',
  () => {
    const view =
      combinedFieldsViewModel({
        currentsEnabled: true,
        windEnabled: true,
        currentsLoading: true,
        windError: 'boom',
      });

    assert.equal(
      view.state,
      'error',
    );
  },
);


test(
  'field time delta is absolute and rounded to minutes',
  () => {
    assert.equal(
      combinedFieldTimeDeltaMinutes(
        '2026-09-19T09:00:00Z',
        '2026-09-19T10:31:20Z',
      ),
      91,
    );

    assert.equal(
      combinedFieldTimeDeltaMinutes(
        '2026-09-19T10:31:20Z',
        '2026-09-19T09:00:00Z',
      ),
      91,
    );
  },
);


test(
  'field time delta is null for incomplete timestamps',
  () => {
    assert.equal(
      combinedFieldTimeDeltaMinutes(
        null,
        '2026-09-19T09:00:00Z',
      ),
      null,
    );
  },
);


test(
  'display modes are normalized defensively',
  () => {
    assert.equal(
      normalizeCombinedDisplayMode(
        'particles',
      ),
      'particles',
    );

    assert.equal(
      normalizeCombinedDisplayMode(
        'invalid',
      ),
      'arrows',
    );
  },
);


test(
  'combined wind mean speed uses backend speed stats when available',
  () => {
    assert.equal(
      combinedWindMeanSpeedMs({
        speed_stats: {
          mean_speed_ms: 4.25,
        },
        vectors: [
          { speed: 1 },
          { speed: 9 },
        ],
      }),
      4.25,
    );
  },
);


test(
  'combined wind mean speed falls back to normalized vectors',
  () => {
    assert.equal(
      combinedWindMeanSpeedMs({
        vectors: [
          { speed: 2 },
          { speed: 4 },
          { speed: 6 },
        ],
      }),
      4,
    );
  },
);


test(
  'combined wind mean speed is null without valid wind speeds',
  () => {
    assert.equal(
      combinedWindMeanSpeedMs({
        vectors: [
          { speed: null },
          { speed: -1 },
          { speed: 'bad' },
        ],
      }),
      null,
    );
  },
);


test(
  'ready combined view exposes field-wide wind mean speed',
  () => {
    const view =
      combinedFieldsViewModel({
        currentsEnabled: true,
        windEnabled: true,
        currentsPayload: {
          valid_time:
            '2026-09-19T10:00:00Z',
        },
        windPayload: {
          valid_time:
            '2026-09-19T10:34:00Z',
          speed_stats: {
            mean_speed_ms: 3.649093,
          },
        },
      });

    assert.equal(
      view.windMeanSpeedMs,
      3.649093,
    );
  },
);
