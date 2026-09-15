import test from 'node:test';
import assert from 'node:assert/strict';

import {
  coordinateInterpretation,
  eventDetailsViewModel,
  humanizeToken,
  locationScopeLabel,
  safeExternalHttpUrl,
} from './eventDetails.js';

test('builds operator-friendly event details', () => {
  const vm = eventDetailsViewModel({
    id: 'evt_001',
    category: 'industrial_fire',
    categoryLabel: 'Industrial fire',
    markerColor: '#ff5d5d',
    locationName: 'Gelendzhik',
    primaryTitle: 'Substation fire',
    status: 'contained',
    severity: 'medium',
    confidence: 0.84,
    evidenceCount: 3,
    latitude: 44.5609,
    longitude: 38.0767,
    firstSeen: '2026-09-13T10:00:00Z',
    lastSeen: '2026-09-13T11:00:00Z',
  });

  assert.equal(vm.category, 'Industrial fire');
  assert.equal(vm.location, 'Gelendzhik');
  assert.equal(vm.status, 'Contained');
  assert.equal(vm.severity, 'Medium');
  assert.equal(vm.confidence, '84%');
  assert.equal(vm.evidenceCount, 3);
  assert.equal(vm.coordinates, '44.5609, 38.0767');
});

test('builds data quality labels for canonical coordinates', () => {
  const vm = eventDetailsViewModel({
    locationType: 'protected_area',
    locationConfidence: 0.91,
    coordinateSource: 'canonical_database',
    incidentTime: null,
    detectionTime: '2026-09-12T22:30:48Z',
    sourceTime: '2026-09-09T18:05:18Z',
  });

  assert.equal(vm.locationType, 'Protected Area');
  assert.equal(vm.locationScope, 'Protected-area');
  assert.equal(vm.locationConfidence, '91%');
  assert.equal(vm.coordinateSource, 'Canonical Database');
  assert.match(vm.coordinateInterpretation, /Representative map point/);
  assert.equal(vm.incidentTime, '—');
  assert.notEqual(vm.detectionTime, '—');
  assert.notEqual(vm.sourceTime, '—');
});

test('maps water bodies to a water-body scope label', () => {
  assert.equal(
    locationScopeLabel('water_body'),
    'Water-body',
  );

  assert.match(
    coordinateInterpretation({ coordinateSource: 'canonical_database' }),
    /not exact incident coordinates/,
  );
});

test('humanizes machine tokens', () => {
  assert.equal(
    humanizeToken('marine_animal_death'),
    'Marine Animal Death',
  );
});

test('accepts only external http and https evidence URLs', () => {
  assert.equal(
    safeExternalHttpUrl('javascript:alert(1)'),
    null,
  );

  assert.equal(
    safeExternalHttpUrl('https://example.com/news'),
    'https://example.com/news',
  );
});
