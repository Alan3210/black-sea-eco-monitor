import test from 'node:test';
import assert from 'node:assert/strict';

import {
  fetchInvestigation,
} from './investigationApi.js';


test(
  'fetches investigation data from context link',
  async () => {
    const calls = [];

    const payload = {
      event_id: 'evt_123',
      evidence: [],
      candidate_sources: [],
    };

    const result =
      await fetchInvestigation(
        '/monitor/events/evt_123/investigation',
        async (href, options) => {
          calls.push({
            href,
            options,
          });

          return {
            ok: true,
            status: 200,

            async json() {
              return payload;
            },
          };
        },
      );

    assert.deepEqual(
      result,
      payload,
    );

    assert.equal(
      calls[0].href,
      '/monitor/events/evt_123/investigation',
    );

    assert.equal(
      calls[0].options.headers.Accept,
      'application/json',
    );
  },
);


test(
  'returns null when investigation link is absent',
  async () => {
    const result =
      await fetchInvestigation(
        null,
        async () => {
          throw new Error(
            'fetch should not be called',
          );
        },
      );

    assert.equal(
      result,
      null,
    );
  },
);


test(
  'throws on investigation API errors',
  async () => {
    await assert.rejects(
      () =>
        fetchInvestigation(
          '/monitor/events/evt_123/investigation',
          async () => ({
            ok: false,
            status: 503,
          }),
        ),
      /Investigation API returned HTTP 503/,
    );
  },
);