import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildWindFieldUrl,
  fetchWindField,
  formatWindSpeed,
  normalizeWindArrowSizePercent,
  normalizeWindFieldPayload,
  windArrowSizeExpression,
  windToFeatureCollection,
} from './wind.js';


test(
  'normalizes wind arrow size values',
  () => {
    assert.equal(
      normalizeWindArrowSizePercent(
        37,
      ),
      60,
    );
    assert.equal(
      normalizeWindArrowSizePercent(
        143,
      ),
      140,
    );
    assert.equal(
      normalizeWindArrowSizePercent(
        260,
      ),
      200,
    );
  },
);


test(
  'wind arrow size expression scales with wind speed',
  () => {
    const expression =
      windArrowSizeExpression(
        100,
      );

    assert.deepEqual(
      expression.slice(0, 3),
      [
        'interpolate',
        ['linear'],
        ['get', 'speed'],
      ],
    );
    assert.equal(
      expression.at(-2),
      15,
    );
    assert.equal(
      expression.at(-1),
      1.3,
    );
  },
);


test(
  'builds wind field URL with default stride',
  () => {
    assert.equal(
      buildWindFieldUrl(),
      '/weather/wind-field?stride=2',
    );
  },
);


test(
  'builds wind field URL with requested UTC time',
  () => {
    const url = buildWindFieldUrl({
      at:
        '2026-09-19T08:43:00Z',
      stride: 3,
    });

    const parsed = new URL(
      url,
      'http://localhost',
    );

    assert.equal(
      parsed.pathname,
      '/weather/wind-field',
    );
    assert.equal(
      parsed.searchParams.get(
        'stride',
      ),
      '3',
    );
    assert.equal(
      parsed.searchParams.get(
        'at',
      ),
      '2026-09-19T08:43:00Z',
    );
  },
);


test(
  'normalizes valid wind vectors and rejects incomplete rows',
  () => {
    const payload =
      normalizeWindFieldPayload({
        provider: 'ecmwf',
        model: 'ifs',
        vectors: [
          {
            latitude: 44.6,
            longitude: 37.8,
            u_ms: -2,
            v_ms: -3,
            speed_ms: 3.6055,
            direction_from_deg: 33,
            direction_to_deg: 213,
          },
          {
            latitude: 44.7,
            longitude: 37.9,
            u_ms: null,
            v_ms: 1,
            speed_ms: 1,
            direction_from_deg: 180,
            direction_to_deg: 0,
          },
        ],
      });

    assert.equal(
      payload.vector_count,
      1,
    );
    assert.deepEqual(
      payload.vectors[0],
      {
        latitude: 44.6,
        longitude: 37.8,
        u: -2,
        v: -3,
        speed: 3.6055,
        direction_from_deg: 33,
        direction_to_deg: 213,
      },
    );
  },
);


test(
  'normalizes directions into zero-to-360 range',
  () => {
    const payload =
      normalizeWindFieldPayload({
        vectors: [
          {
            latitude: 44,
            longitude: 38,
            u_ms: 1,
            v_ms: 2,
            speed_ms: 2.2,
            direction_from_deg: -10,
            direction_to_deg: 530,
          },
        ],
      });

    assert.equal(
      payload.vectors[0]
        .direction_from_deg,
      350,
    );
    assert.equal(
      payload.vectors[0]
        .direction_to_deg,
      170,
    );
  },
);


test(
  'GeoJSON rotates wind arrows by physical TO direction',
  () => {
    const geojson =
      windToFeatureCollection({
        vectors: [
          {
            latitude: 44.6,
            longitude: 37.8,
            u_ms: -2,
            v_ms: -3.464,
            speed_ms: 4,
            direction_from_deg: 30,
            direction_to_deg: 210,
          },
        ],
      });

    assert.equal(
      geojson.features.length,
      1,
    );
    assert.equal(
      geojson.features[0]
        .properties
        .direction_from_deg,
      30,
    );
    assert.equal(
      geojson.features[0]
        .properties
        .direction_to_deg,
      210,
    );
  },
);


test(
  'normalized wind payload remains renderable as GeoJSON',
  () => {
    const raw = {
      provider: 'ecmwf',
      model: 'ifs',
      vectors: [
        {
          latitude: 44.6,
          longitude: 37.8,
          u_ms: -2,
          v_ms: -3.464,
          speed_ms: 4,
          direction_from_deg: 30,
          direction_to_deg: 210,
        },
      ],
    };

    const normalized =
      normalizeWindFieldPayload(
        raw,
      );

    const normalizedAgain =
      normalizeWindFieldPayload(
        normalized,
      );

    assert.equal(
      normalizedAgain.vector_count,
      1,
    );

    const geojson =
      windToFeatureCollection(
        normalized,
      );

    assert.equal(
      geojson.features.length,
      1,
    );
    assert.deepEqual(
      geojson.features[0]
        .geometry
        .coordinates,
      [37.8, 44.6],
    );
    assert.equal(
      geojson.features[0]
        .properties
        .speed,
      4,
    );
    assert.equal(
      geojson.features[0]
        .properties
        .direction_to_deg,
      210,
    );
  },
);


test(
  'formats wind speed in metres per second',
  () => {
    assert.equal(
      formatWindSpeed(
        4.0538,
      ),
      '4.1 m/s',
    );
    assert.equal(
      formatWindSpeed(
        null,
      ),
      '—',
    );
  },
);


test(
  'fetchWindField surfaces backend detail',
  async () => {
    const fetchImpl = async () => ({
      ok: false,
      status: 503,
      async json() {
        return {
          detail:
            'ECMWF unavailable',
        };
      },
    });

    await assert.rejects(
      () => fetchWindField(
        {},
        fetchImpl,
      ),
      /ECMWF unavailable/,
    );
  },
);
