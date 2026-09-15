import test from 'node:test';
import assert from 'node:assert/strict';

import {
  DEFAULT_DRIFT_HORIZON,
  driftApiUrl,
  driftCenterGeoJSON,
  driftEnvelopeGeoJSON,
  driftPointsGeoJSON,
  driftSeedGeoJSON,
  driftTrackGeoJSON,
  normalizeDriftHorizon,
  normalizeDriftParticles,
  snapshotForHorizon,
} from './drift.js';


test('normalizes supported drift horizons', () => {
  assert.equal(normalizeDriftHorizon(6), 6);
  assert.equal(normalizeDriftHorizon('24'), 24);
  assert.equal(
    normalizeDriftHorizon(18),
    DEFAULT_DRIFT_HORIZON,
  );
});


test('normalizes drift particle count', () => {
  assert.equal(normalizeDriftParticles(50), 100);
  assert.equal(normalizeDriftParticles(340), 300);
  assert.equal(normalizeDriftParticles(1500), 1000);
});


test('builds drift API URL', () => {
  const url = driftApiUrl({
    longitude: 37.7691,
    latitude: 44.724,
    hours: 24,
    particles: 300,
  });

  assert.match(url, /^\/ocean\/drift\/?\?/);
  assert.match(url, /lon=37\.7691/);
  assert.match(url, /lat=44\.724/);
  assert.match(url, /hours=24/);
  assert.match(url, /particles=300/);
});


test('finds snapshot for selected horizon', () => {
  const snapshot = snapshotForHorizon(
    {
      horizons: [
        { hours: 6 },
        { hours: 12 },
        { hours: 24 },
      ],
    },
    12,
  );

  assert.deepEqual(snapshot, { hours: 12 });
});


test('converts drift seed and center to GeoJSON', () => {
  const seed = driftSeedGeoJSON({
    longitude: 37.7,
    latitude: 44.7,
  });

  const center = driftCenterGeoJSON({
    hours: 6,
    particle_count: 100,
    center: {
      longitude: 37.8,
      latitude: 44.71,
    },
  });

  assert.equal(seed.features.length, 1);
  assert.equal(center.features.length, 1);
  assert.deepEqual(
    center.features[0].geometry.coordinates,
    [37.8, 44.71],
  );
});


test('converts particle cloud to GeoJSON points', () => {
  const geojson = driftPointsGeoJSON({
    hours: 6,
    points: [
      [37.7, 44.7],
      [37.8, 44.8],
    ],
  });

  assert.equal(geojson.features.length, 2);
  assert.equal(
    geojson.features[0].geometry.type,
    'Point',
  );
});


test('converts drift envelope to polygon GeoJSON', () => {
  const geojson = driftEnvelopeGeoJSON({
    hours: 24,
    envelope: {
      type: 'Polygon',
      coordinates: [[
        [37, 44],
        [38, 44],
        [38, 45],
        [37, 44],
      ]],
    },
  });

  assert.equal(geojson.features.length, 1);
  assert.equal(
    geojson.features[0].geometry.type,
    'Polygon',
  );
});


test('converts mean drift track to LineString', () => {
  const geojson = driftTrackGeoJSON({
    mean_track: [
      { longitude: 37.7, latitude: 44.7 },
      { longitude: 37.8, latitude: 44.71 },
      { longitude: 37.9, latitude: 44.72 },
    ],
  });

  assert.equal(geojson.features.length, 1);
  assert.equal(
    geojson.features[0].geometry.type,
    'LineString',
  );
});


test('limits mean drift track to selected forecast horizon', () => {
  const meanTrack = Array.from(
    { length: 25 },
    (_, index) => ({
      longitude: 37 + index * 0.01,
      latitude: 44 + index * 0.01,
    }),
  );

  const geojson = driftTrackGeoJSON(
    { mean_track: meanTrack },
    6,
  );

  assert.equal(
    geojson.features[0].geometry.coordinates.length,
    7,
  );
});
