import test from 'node:test';
import assert from 'node:assert/strict';

import {
  categoryLabel,
  formatEventCount,
  localizeLocationName,
  normalizeLanguage,
  saveLanguage,
  statusLabel,
  t,
} from './i18n.js';

test('uses Russian as the default interface language', () => {
  assert.equal(
    normalizeLanguage('unsupported'),
    'ru',
  );
});

test('translates core event labels to Russian and English', () => {
  assert.equal(
    categoryLabel('oil_spill', 'ru'),
    'Разлив нефти',
  );
  assert.equal(
    categoryLabel('oil_spill', 'en'),
    'Oil spill',
  );
  assert.equal(
    statusLabel('contained', 'ru'),
    'Локализовано',
  );
});

test('localizes canonical location names without translating unknown source text', () => {
  assert.equal(
    localizeLocationName('Kerch Strait', 'ru'),
    'Керченский пролив',
  );
  assert.equal(
    localizeLocationName('Custom Facility Name', 'ru'),
    'Custom Facility Name',
  );
});

test('formats Russian event-count plurals', () => {
  assert.equal(
    formatEventCount(1, 1, 'ru'),
    '1 событие',
  );
  assert.equal(
    formatEventCount(2, 2, 'ru'),
    '2 события',
  );
  assert.equal(
    formatEventCount(5, 5, 'ru'),
    '5 событий',
  );
  assert.equal(
    formatEventCount(11, 11, 'ru'),
    '11 событий',
  );
  assert.equal(
    formatEventCount(21, 21, 'ru'),
    '21 событие',
  );
});

test('persists the selected language through a storage-like adapter', () => {
  const values = new Map();

  const storage = {
    getItem(key) {
      return values.get(key) ?? null;
    },
    setItem(key, value) {
      values.set(key, value);
    },
  };

  assert.equal(
    saveLanguage('en', storage),
    'en',
  );

  assert.equal(
    values.get('blackSeaEcoMonitor.language'),
    'en',
  );

  assert.equal(
    t('ru', 'connection.updated', { time: '10:15:00' }),
    'Обновлено 10:15:00',
  );
});
