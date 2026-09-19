import assert from 'node:assert/strict';
import test from 'node:test';

import {
  DEFAULT_DRIFT_FORCING_MODE,
  DRIFT_FORCING_CURRENT_ONLY,
  DRIFT_FORCING_CURRENTS_PLUS_WIND,
  driftApiUrl,
  driftForcingViewModel,
  normalizeDriftForcingMode,
} from './drift.js';


test('WEATHER-1.4 keeps current_only as the default', () => {
  assert.equal(
    DEFAULT_DRIFT_FORCING_MODE,
    DRIFT_FORCING_CURRENT_ONLY,
  );
  assert.equal(
    normalizeDriftForcingMode(null),
    DRIFT_FORCING_CURRENT_ONLY,
  );
});


test('WEATHER-1.4 accepts currents_plus_wind', () => {
  assert.equal(
    normalizeDriftForcingMode('currents_plus_wind'),
    DRIFT_FORCING_CURRENTS_PLUS_WIND,
  );
});


test('WEATHER-1.4 safely falls back for an unknown mode', () => {
  assert.equal(
    normalizeDriftForcingMode('unknown-mode'),
    DRIFT_FORCING_CURRENT_ONLY,
  );
});


test('WEATHER-1.4 API URL sends current_only by default', () => {
  const url = new URL(
    driftApiUrl({
      longitude: 37.8,
      latitude: 44.6,
      hours: 6,
      particles: 100,
    }),
    'http://localhost',
  );

  assert.equal(
    url.searchParams.get('forcing_mode'),
    'current_only',
  );
});


test('WEATHER-1.4 API URL sends currents_plus_wind explicitly', () => {
  const url = new URL(
    driftApiUrl({
      longitude: 37.8,
      latitude: 44.6,
      hours: 6,
      particles: 100,
      forcingMode: DRIFT_FORCING_CURRENTS_PLUS_WIND,
    }),
    'http://localhost',
  );

  assert.equal(
    url.searchParams.get('forcing_mode'),
    'currents_plus_wind',
  );
});


test('WEATHER-1.4 exposes ECMWF provenance and 2 percent windage', () => {
  const view = driftForcingViewModel(
    {
      forcing_mode: 'currents_plus_wind',
      simulation: {
        wind_drift_factor: 0.02,
      },
      forcing: {
        wind: {
          provider: 'ecmwf',
          model: 'ifs',
          forecast_reference_time:
            '2026-09-19T00:00:00+00:00',
          sources: ['google'],
          fallback_used: false,
        },
      },
    },
    DRIFT_FORCING_CURRENT_ONLY,
  );

  assert.equal(view.windEnabled, true);
  assert.equal(view.windDriftFactor, 0.02);
  assert.equal(view.provider, 'ecmwf');
  assert.equal(view.model, 'ifs');
  assert.deepEqual(view.sources, ['google']);
  assert.equal(
    view.forecastReferenceTime,
    '2026-09-19T00:00:00+00:00',
  );
});
