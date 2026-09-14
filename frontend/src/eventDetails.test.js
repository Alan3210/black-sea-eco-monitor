import test from 'node:test';
import assert from 'node:assert/strict';

import {
  eventDetailsViewModel,
  humanizeToken,
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
