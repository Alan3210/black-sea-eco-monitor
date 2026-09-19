import assert from 'node:assert/strict';
import test from 'node:test';

import {
  advectWindPosition,
  buildWindVectorField,
  normalizeWindDisplayMode,
  normalizeWindParticleCount,
  normalizeWindParticleSpeedPercent,
  normalizeWindParticleTrailPercent,
  normalizeWindParticleSizePercent,
  sampleWindVector,
  windParticleSeedBounds,
  windParticleStrokeStyle,
  windTrailRetention,
} from './windParticles.js';


test(
  'normalizes wind particle count',
  () => {
    assert.equal(
      normalizeWindParticleCount(
        50,
      ),
      400,
    );

    assert.equal(
      normalizeWindParticleCount(
        2501,
      ),
      2400,
    );

    assert.equal(
      normalizeWindParticleCount(
        1151,
      ),
      1200,
    );
  },
);


test(
  'normalizes wind particle animation speed',
  () => {
    assert.equal(
      normalizeWindParticleSpeedPercent(
        10,
      ),
      50,
    );

    assert.equal(
      normalizeWindParticleSpeedPercent(
        220,
      ),
      200,
    );

    assert.equal(
      normalizeWindParticleSpeedPercent(
        126,
      ),
      130,
    );
  },
);


test(
  'normalizes wind particle trail percentage',
  () => {
    assert.equal(
      normalizeWindParticleTrailPercent(
        0,
      ),
      10,
    );

    assert.equal(
      normalizeWindParticleTrailPercent(
        140,
      ),
      100,
    );

    assert.equal(
      normalizeWindParticleTrailPercent(
        54,
      ),
      50,
    );
  },
);


test(
  'normalizes wind display modes',
  () => {
    assert.equal(
      normalizeWindDisplayMode(
        'arrows',
      ),
      'arrows',
    );

    assert.equal(
      normalizeWindDisplayMode(
        'particles',
      ),
      'particles',
    );

    assert.equal(
      normalizeWindDisplayMode(
        'both',
      ),
      'both',
    );

    assert.equal(
      normalizeWindDisplayMode(
        'invalid',
      ),
      'arrows',
    );
  },
);


test(
  'builds and samples wind vector field',
  () => {
    const field =
      buildWindVectorField([
        {
          longitude: 37.0,
          latitude: 44.0,
          u: 2,
          v: -3,
          speed: 3.6,
        },
        {
          longitude: 37.5,
          latitude: 44.0,
          u: 4,
          v: -1,
          speed: 4.1,
        },
      ]);

    assert.equal(
      field.vectors.length,
      2,
    );

    const sample =
      sampleWindVector(
        field,
        37.03,
        44.02,
      );

    assert.ok(
      sample,
    );

    assert.equal(
      sample.u,
      2,
    );
  },
);


test(
  'does not sample wind far outside field',
  () => {
    const field =
      buildWindVectorField([
        {
          longitude: 37,
          latitude: 44,
          u: 2,
          v: 1,
          speed: 2.2,
        },
      ]);

    assert.equal(
      sampleWindVector(
        field,
        50,
        55,
      ),
      null,
    );
  },
);


test(
  'advects wind particle east and north from u and v',
  () => {
    const result =
      advectWindPosition(
        {
          longitude: 37,
          latitude: 44,
        },
        {
          u: 4,
          v: 2,
          speed: 4.5,
        },
        1,
        100,
      );

    assert.ok(
      result.longitude > 37,
    );

    assert.ok(
      result.latitude > 44,
    );
  },
);


test(
  'wind animation speed scales advection distance',
  () => {
    const slow =
      advectWindPosition(
        {
          longitude: 37,
          latitude: 44,
        },
        {
          u: 4,
          v: 0,
          speed: 4,
        },
        1,
        50,
      );

    const fast =
      advectWindPosition(
        {
          longitude: 37,
          latitude: 44,
        },
        {
          u: 4,
          v: 0,
          speed: 4,
        },
        1,
        200,
      );

    assert.ok(
      (
        fast.longitude - 37
      )
      > (
        slow.longitude - 37
      ),
    );
  },
);


test(
  'wind trail retention remains bounded',
  () => {
    const short =
      windTrailRetention(
        10,
      );

    const long =
      windTrailRetention(
        100,
      );

    assert.ok(
      short > 0
      && short < 1,
    );

    assert.ok(
      long > short
      && long < 1,
    );
  },
);


test(
  'stronger wind draws a wider particle stroke',
  () => {
    const weak =
      windParticleStrokeStyle(
        1,
      );

    const strong =
      windParticleStrokeStyle(
        15,
      );

    assert.match(
      weak.color,
      /^hsla\(/,
    );

    assert.ok(
      strong.width
      > weak.width,
    );
  },
);


test(
  'limits wind particle seeding to the visible map viewport',
  () => {
    const field =
      buildWindVectorField([
        {
          longitude: 27,
          latitude: 40,
          u: 1,
          v: 1,
          speed: 1.4,
        },
        {
          longitude: 42,
          latitude: 47,
          u: 1,
          v: 1,
          speed: 1.4,
        },
      ]);

    const bounds =
      windParticleSeedBounds(
        field,
        {
          west: 36,
          east: 39,
          south: 43,
          north: 45,
        },
        0.1,
      );

    assert.ok(
      bounds,
    );

    assert.ok(
      bounds.west >= 35.7,
    );

    assert.ok(
      bounds.east <= 39.3,
    );

    assert.ok(
      bounds.south >= 42.8,
    );

    assert.ok(
      bounds.north <= 45.2,
    );

    assert.ok(
      (
        bounds.east
        - bounds.west
      )
      < (
        field.maxLongitude
        - field.minLongitude
      ),
    );
  },
);


test(
  'normalizes wind particle size percentage',
  () => {
    assert.equal(
      normalizeWindParticleSizePercent(
        20,
      ),
      60,
    );

    assert.equal(
      normalizeWindParticleSizePercent(
        260,
      ),
      200,
    );

    assert.equal(
      normalizeWindParticleSizePercent(
        127,
      ),
      130,
    );
  },
);


test(
  'wind particle size scales both core and contrast halo',
  () => {
    const small =
      windParticleStrokeStyle(
        8,
        60,
      );

    const large =
      windParticleStrokeStyle(
        8,
        200,
      );

    assert.ok(
      large.width
      > small.width,
    );

    assert.ok(
      large.haloWidth
      > small.haloWidth,
    );

    assert.ok(
      small.haloWidth
      > small.width,
    );

    assert.match(
      small.haloColor,
      /^rgba\(/,
    );
  },
);
