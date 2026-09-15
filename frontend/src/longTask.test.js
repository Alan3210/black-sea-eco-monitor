import test from 'node:test';
import assert from 'node:assert/strict';

import {
  formatElapsedSeconds,
  longTaskViewModel,
  normalizeElapsedSeconds,
} from './longTask.js';


test('normalizes invalid elapsed values to zero', () => {
  assert.equal(normalizeElapsedSeconds(-5), 0);
  assert.equal(normalizeElapsedSeconds('bad'), 0);
  assert.equal(normalizeElapsedSeconds(7.9), 7);
});


test('formats elapsed time as mm:ss', () => {
  assert.equal(formatElapsedSeconds(0), '0:00');
  assert.equal(formatElapsedSeconds(65), '1:05');
});


test('formats long elapsed time with hours', () => {
  assert.equal(formatElapsedSeconds(3661), '1:01:01');
});


test('delays long-task UI to avoid flashing on fast requests', () => {
  assert.equal(
    longTaskViewModel({ startedAtMs: null }).active,
    false,
  );

  const view = longTaskViewModel({
    startedAtMs: 1000,
    nowMs: 1300,
    revealAfterMs: 500,
  });

  assert.equal(view.active, true);
  assert.equal(view.visible, false);
  assert.equal(view.elapsedText, '0:00');
});


test('marks a request as slow after its threshold', () => {
  const view = longTaskViewModel({
    startedAtMs: 1000,
    nowMs: 122000,
    revealAfterMs: 500,
    slowAfterSeconds: 120,
  });

  assert.equal(view.visible, true);
  assert.equal(view.slow, true);
  assert.equal(view.elapsedText, '2:01');
});
