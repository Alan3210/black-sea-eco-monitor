import test from 'node:test';
import assert from 'node:assert/strict';

import {
  BLACK_SEA_CENTER,
  BLACK_SEA_MIN_ZOOM,
  BLACK_SEA_NAVIGATION_BOUNDS,
  REGIONAL_FADE_BANDS,
  isInsideRegionalFocus,
  regionalFocusFeatureCollection,
} from './regionalFocus.js';


test('keeps the Black Sea center inside the 500 km focus core', () => {
  assert.equal(
    isInsideRegionalFocus(
      BLACK_SEA_CENTER[0],
      BLACK_SEA_CENTER[1],
      500,
    ),
    true,
  );
});


test('keeps representative Black Sea coastal cities inside the 500 km core', () => {
  const places = [
    [37.7691, 44.7240], // Novorossiysk
    [39.7231, 43.5855], // Sochi
    [33.5221, 44.6054], // Sevastopol
    [36.5000, 45.3000], // Kerch Strait
    [29.0, 41.0],       // Istanbul / Bosporus area
  ];

  for (const [longitude, latitude] of places) {
    assert.equal(
      isInsideRegionalFocus(longitude, latitude, 500),
      true,
    );
  }
});


test('fades remote Europe outside the Black Sea 500 km core', () => {
  assert.equal(
    isInsideRegionalFocus(13.405, 52.52, 500), // Berlin
    false,
  );

  assert.equal(
    isInsideRegionalFocus(2.3522, 48.8566, 500), // Paris
    false,
  );
});


test('builds progressive regional fade mask features', () => {
  const collection = regionalFocusFeatureCollection();

  assert.equal(collection.type, 'FeatureCollection');
  assert.equal(collection.features.length, REGIONAL_FADE_BANDS.length);
  assert.deepEqual(
    REGIONAL_FADE_BANDS.map((band) => band.distanceKm),
    [500, 600, 700, 800, 950],
  );

  for (const feature of collection.features) {
    assert.equal(feature.geometry.type, 'Polygon');
    assert.equal(feature.geometry.coordinates.length, 2);
  }
});


test('increases fade opacity away from the regional core', () => {
  for (let index = 1; index < REGIONAL_FADE_BANDS.length; index += 1) {
    assert.ok(
      REGIONAL_FADE_BANDS[index].opacity
      > REGIONAL_FADE_BANDS[index - 1].opacity,
    );
  }
});


test('uses regional navigation bounds and prevents world-scale zoom-out', () => {
  const [[west, south], [east, north]] = BLACK_SEA_NAVIGATION_BOUNDS;

  assert.ok(west < 22);
  assert.ok(east > 47);
  assert.ok(south < 37);
  assert.ok(north > 51);
  assert.ok(BLACK_SEA_MIN_ZOOM >= 4.5);
});
