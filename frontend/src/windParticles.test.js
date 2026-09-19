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
  'builds and samples a regular wind vector grid',
  () => {
    const field =
      buildWindVectorField([
        {
          longitude: 37.0,
          latitude: 44.0,
          u: 2,
          v: -3,
          speed: Math.hypot(
            2,
            -3,
          ),
        },
        {
          longitude: 37.5,
          latitude: 44.0,
          u: 4,
          v: -1,
          speed: Math.hypot(
            4,
            -1,
          ),
        },
        {
          longitude: 37.0,
          latitude: 44.5,
          u: 3,
          v: -2,
          speed: Math.hypot(
            3,
            -2,
          ),
        },
        {
          longitude: 37.5,
          latitude: 44.5,
          u: 5,
          v: 0,
          speed: 5,
        },
      ]);

    assert.equal(
      field.vectors.length,
      4,
    );

    assert.equal(
      field.isRegularGrid,
      true,
    );

    const sample =
      sampleWindVector(
        field,
        37.25,
        44.25,
      );

    assert.ok(
      sample,
    );

    assert.ok(
      Math.abs(
        sample.u - 3.5,
      ) < 1e-9,
    );

    assert.ok(
      Math.abs(
        sample.v + 1.5,
      ) < 1e-9,
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


test(
  'bilinearly interpolates u and v inside a wind grid cell',
  () => {
    const field =
      buildWindVectorField([
        {
          longitude: 0,
          latitude: 0,
          u: 0,
          v: 0,
          speed: 0,
        },
        {
          longitude: 1,
          latitude: 0,
          u: 10,
          v: 0,
          speed: 10,
        },
        {
          longitude: 0,
          latitude: 1,
          u: 0,
          v: 20,
          speed: 20,
        },
        {
          longitude: 1,
          latitude: 1,
          u: 10,
          v: 20,
          speed: Math.hypot(
            10,
            20,
          ),
        },
      ]);

    const sample =
      sampleWindVector(
        field,
        0.25,
        0.75,
      );

    assert.ok(
      sample,
    );

    assert.ok(
      Math.abs(
        sample.u - 2.5,
      ) < 1e-9,
    );

    assert.ok(
      Math.abs(
        sample.v - 15,
      ) < 1e-9,
    );

    assert.ok(
      Math.abs(
        sample.speed
        - Math.hypot(
          2.5,
          15,
        ),
      ) < 1e-9,
    );
  },
);


test(
  'keeps particle wind sampling continuous across grid-cell seams',
  () => {
    const vectors = [];

    for (
      const latitude
      of [
        44,
        44.5,
      ]
    ) {
      for (
        const longitude
        of [
          37,
          37.5,
          38,
        ]
      ) {
        const u =
          (
            longitude - 37
          ) * 10;

        const v =
          (
            latitude - 44
          ) * 6;

        vectors.push({
          longitude,
          latitude,
          u,
          v,
          speed:
            Math.hypot(
              u,
              v,
            ),
        });
      }
    }

    const field =
      buildWindVectorField(
        vectors,
      );

    const left =
      sampleWindVector(
        field,
        37.5 - 1e-5,
        44.25,
      );

    const right =
      sampleWindVector(
        field,
        37.5 + 1e-5,
        44.25,
      );

    assert.ok(
      left,
    );

    assert.ok(
      right,
    );

    assert.ok(
      Math.abs(
        left.u - right.u,
      ) < 0.001,
    );

    assert.ok(
      Math.abs(
        left.v - right.v,
      ) < 0.001,
    );
  },
);


test(
  'uses smooth inverse-distance fallback for an incomplete grid',
  () => {
    const field =
      buildWindVectorField([
        {
          longitude: 37,
          latitude: 44,
          u: 0,
          v: 0,
          speed: 0,
        },
        {
          longitude: 37.5,
          latitude: 44,
          u: 10,
          v: 0,
          speed: 10,
        },
        {
          longitude: 37,
          latitude: 44.5,
          u: 0,
          v: 10,
          speed: 10,
        },
      ]);

    assert.equal(
      field.isRegularGrid,
      false,
    );

    const sample =
      sampleWindVector(
        field,
        37.2,
        44.2,
      );

    assert.ok(
      sample,
    );

    assert.ok(
      sample.u > 0
      && sample.u < 10,
    );

    assert.ok(
      sample.v > 0
      && sample.v < 10,
    );
  },
);
