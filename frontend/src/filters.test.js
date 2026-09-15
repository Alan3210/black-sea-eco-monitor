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
    incidentTime: null,
    sourceTime: null,
    detectionTime: null,
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

test('prefers incident time over system update timestamps', () => {
  const row = event({
    incidentTime: '2026-09-10T06:00:00Z',
    sourceTime: '2026-09-13T08:00:00Z',
    detectionTime: '2026-09-13T09:00:00Z',
    lastSeen: '2026-09-13T10:00:00Z',
  });

  assert.equal(
    eventReferenceTime(row),
    Date.parse('2026-09-10T06:00:00Z'),
  );
});

test('falls back from source time to detection time before legacy timestamps', () => {
  assert.equal(
    eventReferenceTime(event({
      sourceTime: '2026-09-11T06:00:00Z',
      detectionTime: '2026-09-12T06:00:00Z',
      lastSeen: '2026-09-13T06:00:00Z',
    })),
    Date.parse('2026-09-11T06:00:00Z'),
  );

  assert.equal(
    eventReferenceTime(event({
      sourceTime: null,
      detectionTime: '2026-09-12T06:00:00Z',
      lastSeen: '2026-09-13T06:00:00Z',
    })),
    Date.parse('2026-09-12T06:00:00Z'),
  );
});

test('filters by time window using data quality reference time', () => {
  const rows = [
    event({
      id: 'fresh',
      sourceTime: '2026-09-13T06:00:00Z',
      lastSeen: '2026-09-13T07:00:00Z',
    }),
    event({
      id: 'old',
      sourceTime: '2026-09-10T06:00:00Z',
      lastSeen: '2026-09-13T07:00:00Z',
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
