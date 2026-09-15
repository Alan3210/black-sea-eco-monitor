import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildCurrentsUrl,
  cardinalDirection,
  currentArrowSizeExpression,
  currentsToFeatureCollection,
  formatCurrentSpeed,
  normalizeCurrentArrowSizePercent,
  normalizeCurrentsPayload,
} from './currents.js';


test('builds a proxied currents API URL', () => {
  assert.equal(
    buildCurrentsUrl({ stride: 12 }),
    '/ocean/currents/?stride=12',
  );
});


test('normalizes and filters current vectors', () => {
  const result = normalizeCurrentsPayload({
    dataset_id: 'dataset',
    valid_time: '2026-09-15T08:00:00+00:00',
    vectors: [
      {
        longitude: 35,
        latitude: 44,
        u: 0.1,
        v: 0.2,
        speed: 0.2236,
        direction_deg: 26.57,
      },
      {
        longitude: null,
        latitude: 44,
        u: 0.1,
        v: 0.2,
        speed: 0.2236,
        direction_deg: 26.57,
      },
    ],
  });

  assert.equal(result.vector_count, 1);
  assert.equal(result.vectors[0].longitude, 35);
});


test('converts currents to GeoJSON points', () => {
  const collection = currentsToFeatureCollection({
    vectors: [
      {
        longitude: 36.5,
        latitude: 45.3,
        u: 0.12,
        v: -0.04,
        speed: 0.126,
        direction_deg: 108.4,
      },
    ],
  });

  assert.equal(collection.type, 'FeatureCollection');
  assert.equal(collection.features.length, 1);
  assert.deepEqual(
    collection.features[0].geometry.coordinates,
    [36.5, 45.3],
  );
  assert.equal(
    collection.features[0].properties.direction_deg,
    108.4,
  );
});


test('formats cardinal direction in RU and EN', () => {
  assert.equal(cardinalDirection(0, 'ru'), 'С');
  assert.equal(cardinalDirection(90, 'ru'), 'В');
  assert.equal(cardinalDirection(225, 'en'), 'SW');
});


test('formats current speed in metres per second', () => {
  assert.equal(formatCurrentSpeed(0.1555), '0.16 m/s');
  assert.equal(formatCurrentSpeed(null), '—');
});


test('normalizes current arrow size slider values', () => {
  assert.equal(
    normalizeCurrentArrowSizePercent(100),
    100,
  );
  assert.equal(
    normalizeCurrentArrowSizePercent(53),
    60,
  );
  assert.equal(
    normalizeCurrentArrowSizePercent(213),
    200,
  );
  assert.equal(
    normalizeCurrentArrowSizePercent('147'),
    150,
  );
});


test('scales MapLibre current arrow size expression', () => {
  const normal = currentArrowSizeExpression(100);
  const large = currentArrowSizeExpression(200);

  assert.equal(normal[4], 0.72);
  assert.equal(large[4], 1.44);
  assert.equal(large.at(-1), 2.56);
});
