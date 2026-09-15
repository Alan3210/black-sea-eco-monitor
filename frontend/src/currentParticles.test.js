import test from 'node:test';
import assert from 'node:assert/strict';

import {
  advectPosition,
  buildCurrentVectorField,
  normalizeCurrentDisplayMode,
  normalizeParticleCount,
  normalizeParticleSpeedPercent,
  normalizeParticleTrailPercent,
  particleStrokeStyle,
  sampleCurrentVector,
  trailRetention,
} from './currentParticles.js';


test('normalizes particle count', () => {
  assert.equal(
    normalizeParticleCount(1800),
    1800,
  );

  assert.equal(
    normalizeParticleCount(100),
    600,
  );

  assert.equal(
    normalizeParticleCount(3300),
    3000,
  );

  assert.equal(
    normalizeParticleCount('1749'),
    1700,
  );
});


test('normalizes particle animation speed', () => {
  assert.equal(
    normalizeParticleSpeedPercent(100),
    100,
  );

  assert.equal(
    normalizeParticleSpeedPercent(20),
    50,
  );

  assert.equal(
    normalizeParticleSpeedPercent(220),
    200,
  );
});


test('normalizes particle trail percentage', () => {
  assert.equal(
    normalizeParticleTrailPercent(70),
    70,
  );

  assert.equal(
    normalizeParticleTrailPercent(2),
    10,
  );

  assert.equal(
    normalizeParticleTrailPercent(120),
    100,
  );
});


test('normalizes current display modes', () => {
  assert.equal(
    normalizeCurrentDisplayMode('arrows'),
    'arrows',
  );

  assert.equal(
    normalizeCurrentDisplayMode('particles'),
    'particles',
  );

  assert.equal(
    normalizeCurrentDisplayMode('both'),
    'both',
  );

  assert.equal(
    normalizeCurrentDisplayMode('bad'),
    'arrows',
  );
});


test('builds and samples a spatial current field', () => {
  const field =
    buildCurrentVectorField([
      {
        longitude: 35,
        latitude: 44,
        u: 0.2,
        v: 0.1,
        speed: 0.2236,
      },
      {
        longitude: 35.25,
        latitude: 44,
        u: -0.1,
        v: 0.05,
        speed: 0.1118,
      },
    ]);

  assert.equal(
    field.vectors.length,
    2,
  );

  const sampled =
    sampleCurrentVector(
      field,
      35.03,
      44.02,
    );

  assert.ok(sampled);
  assert.equal(
    sampled.longitude,
    35,
  );
});


test('does not sample current far away from the model field', () => {
  const field =
    buildCurrentVectorField([
      {
        longitude: 35,
        latitude: 44,
        u: 0.2,
        v: 0.1,
        speed: 0.2236,
      },
    ]);

  assert.equal(
    sampleCurrentVector(
      field,
      10,
      10,
    ),
    null,
  );
});


test('advects a particle east and north from u and v components', () => {
  const result =
    advectPosition(
      {
        longitude: 35,
        latitude: 44,
      },
      {
        u: 0.2,
        v: 0.1,
      },
      1 / 60,
      100,
    );

  assert.ok(
    result.longitude > 35,
  );

  assert.ok(
    result.latitude > 44,
  );
});


test('trail retention and stroke styling remain bounded', () => {
  assert.ok(
    trailRetention(10)
    < trailRetention(100),
  );

  const slow =
    particleStrokeStyle(0.01);

  const fast =
    particleStrokeStyle(0.7);

  assert.ok(
    fast.width > slow.width,
  );
});
