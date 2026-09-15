import test from 'node:test';
import assert from 'node:assert/strict';

import {
  eventsToFeatureCollection,
  normalizeMonitorEvent,
  normalizeMonitorEvents,
} from './events.js';

test('normalizes a persisted monitor event', () => {
  const event = normalizeMonitorEvent({
    id: 'evt_001',
    category: 'wildfire',
    location: {
      name: 'Novorossiysk',
      latitude: 44.724,
      longitude: 37.7691,
    },
    status: 'resolved',
    severity: 'medium',
    confidence: 0.9,
    evidence_count: 4,
    primary_title: 'Forest fire near Novorossiysk',
  });

  assert.equal(event.id, 'evt_001');
  assert.equal(event.categoryLabel, 'Wildfire');
  assert.equal(event.locationName, 'Novorossiysk');
  assert.equal(event.latitude, 44.724);
  assert.equal(event.longitude, 37.7691);
  assert.equal(event.evidenceCount, 4);
});

test('normalizes data quality location and time metadata', () => {
  const event = normalizeMonitorEvent({
    id: 'evt_quality',
    category: 'wildfire',
    location: {
      name: 'Utrish Reserve',
      latitude: 44.7605,
      longitude: 37.3854,
      type: 'protected_area',
      confidence: 0.91,
      source: 'canonical_database',
    },
    time: {
      incident_time: null,
      detection_time: '2026-09-12T22:30:48+00:00',
      source_time: '2026-09-09T18:05:18+00:00',
    },
  });

  assert.equal(event.locationType, 'protected_area');
  assert.equal(event.locationConfidence, 0.91);
  assert.equal(event.coordinateSource, 'canonical_database');
  assert.equal(event.incidentTime, null);
  assert.equal(event.detectionTime, '2026-09-12T22:30:48+00:00');
  assert.equal(event.sourceTime, '2026-09-09T18:05:18+00:00');
});

test('rejects events without usable coordinates', () => {
  const events = normalizeMonitorEvents([
    {
      id: 'good',
      category: 'wildfire',
      location: {
        latitude: 44.7,
        longitude: 37.7,
      },
    },
    {
      id: 'bad',
      category: 'wildfire',
      location: {
        latitude: null,
        longitude: null,
      },
    },
  ]);

  assert.deepEqual(
    events.map((event) => event.id),
    ['good'],
  );
});

test('converts normalized events to GeoJSON', () => {
  const events = normalizeMonitorEvents([
    {
      id: 'evt_002',
      category: 'industrial_fire',
      location: {
        name: 'Gelendzhik',
        latitude: 44.5609,
        longitude: 38.0767,
      },
      status: 'resolved',
    },
  ]);

  const geojson = eventsToFeatureCollection(events);

  assert.equal(geojson.type, 'FeatureCollection');
  assert.equal(geojson.features.length, 1);
  assert.deepEqual(
    geojson.features[0].geometry.coordinates,
    [38.0767, 44.5609],
  );
});
