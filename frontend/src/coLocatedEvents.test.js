import test from 'node:test';
import assert from 'node:assert/strict';

import {
  coordinateKey,
  findGroupForEvent,
  groupCoLocatedEvents,
} from './coLocatedEvents.js';

function event(id, latitude, longitude) {
  return {
    id,
    latitude,
    longitude,
    locationName: 'Novorossiysk',
  };
}

test('groups events that share the same canonical map point', () => {
  const groups = groupCoLocatedEvents([
    event('wildfire', 44.724, 37.7691),
    event('industrial-fire', 44.724, 37.7691),
  ]);

  assert.equal(groups.length, 1);
  assert.equal(groups[0].count, 2);
  assert.equal(groups[0].isGroup, true);
  assert.deepEqual(
    groups[0].eventIds,
    ['wildfire', 'industrial-fire'],
  );
});

test('keeps separate map points separate', () => {
  const groups = groupCoLocatedEvents([
    event('novorossiysk', 44.724, 37.7691),
    event('gelendzhik', 44.5609, 38.0767),
  ]);

  assert.equal(groups.length, 2);
  assert.equal(groups[0].isGroup, false);
  assert.equal(groups[1].isGroup, false);
});

test('finds the visible coordinate group for an event', () => {
  const groups = groupCoLocatedEvents([
    event('a', 44.724, 37.7691),
    event('b', 44.724, 37.7691),
  ]);

  const group = findGroupForEvent(groups, 'b');

  assert.equal(
    group.id,
    `point:${coordinateKey(event('b', 44.724, 37.7691))}`,
  );
});
