import test from 'node:test';
import assert from 'node:assert/strict';

import {
  eventReferenceTime,
  filterEvents,
} from './filters.js';

const NOW = Date.parse('2026-09-13T12:00:00Z');

function event(overrides = {}) {
  return {
    id: 'evt',
    status: 'active',
    category: 'wildfire',
    lastSeen: '2026-09-12T12:00:00Z',
    updatedAt: null,
    firstSeen: null,
    ...overrides,
  };
}

test('filters by status and category', () => {
  const rows = [
    event({ id: 'a' }),
    event({
      id: 'b',
      status: 'resolved',
    }),
    event({
      id: 'c',
      category: 'industrial_fire',
    }),
  ];

  const result = filterEvents(rows, {
    statuses: ['active'],
    categories: ['wildfire'],
    days: 'all',
    now: NOW,
  });

  assert.deepEqual(
    result.map((row) => row.id),
    ['a'],
  );
});

test('filters by time window using latest-seen time', () => {
  const rows = [
    event({
      id: 'fresh',
      lastSeen: '2026-09-13T06:00:00Z',
    }),
    event({
      id: 'old',
      lastSeen: '2026-09-10T06:00:00Z',
    }),
  ];

  const result = filterEvents(rows, {
    statuses: ['active'],
    categories: ['wildfire'],
    days: 1,
    now: NOW,
  });

  assert.deepEqual(
    result.map((row) => row.id),
    ['fresh'],
  );
});

test('keeps an event when time metadata is unavailable', () => {
  const row = event({
    lastSeen: null,
    updatedAt: null,
    firstSeen: null,
  });

  assert.equal(
    eventReferenceTime(row),
    null,
  );

  const result = filterEvents([row], {
    statuses: ['active'],
    categories: ['wildfire'],
    days: 1,
    now: NOW,
  });

  assert.equal(result.length, 1);
});
