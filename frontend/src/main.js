import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import './style.css';

import {
  eventsToFeatureCollection,
  fetchEventEvidence,
  fetchMonitorEvents,
} from './events.js';

import {
  filterEvents,
} from './filters.js';

import {
  eventDetailsViewModel,
  formatEventDate,
  safeExternalHttpUrl,
} from './eventDetails.js';

import {
  findGroupForEvent,
  groupCoLocatedEvents,
} from './coLocatedEvents.js';

import {
  formatEventCount,
  loadStoredLanguage,
  localeForLanguage,
  localizeLocationName,
  saveLanguage,
  t,
} from './i18n.js';

import {
  cardinalDirection,
  currentArrowSizeExpression,
  currentsToFeatureCollection,
  fetchOceanCurrents,
  formatCurrentSpeed,
  formatCurrentValidTime,
  normalizeCurrentArrowSizePercent,
} from './currents.js';

import {
  CurrentParticleEngine,
  normalizeCurrentDisplayMode,
  normalizeParticleCount,
  normalizeParticleSpeedPercent,
  normalizeParticleTrailPercent,
} from './currentParticles.js';

import {
  DEFAULT_DRIFT_HORIZON,
  DEFAULT_DRIFT_PARTICLES,
  driftCenterGeoJSON,
  driftEnvelopeGeoJSON,
  driftPointsGeoJSON,
  driftSeedGeoJSON,
  driftTrackGeoJSON,
  fetchDriftForecast,
  normalizeDriftHorizon,
  normalizeDriftParticles,
  snapshotForHorizon,
} from './drift.js';

import {
  BLACK_SEA_CENTER,
  BLACK_SEA_INITIAL_ZOOM,
  BLACK_SEA_MAX_ZOOM,
  BLACK_SEA_MIN_ZOOM,
  BLACK_SEA_NAVIGATION_BOUNDS,
  installRegionalFocus,
} from './regionalFocus.js';

import {
  longTaskViewModel,
} from './longTask.js';

const REFRESH_INTERVAL_MS = 60_000;
const CURRENTS_REFRESH_INTERVAL_MS = 15 * 60_000;
const CURRENTS_STRIDE = 10;
const CURRENT_ARROW_SIZE_STORAGE_KEY =
  'black-sea-eco-monitor.current-arrow-size';

const CURRENT_DISPLAY_MODE_STORAGE_KEY =
  'black-sea-eco-monitor.current-display-mode';

const PARTICLE_COUNT_STORAGE_KEY =
  'black-sea-eco-monitor.particle-count';

const PARTICLE_SPEED_STORAGE_KEY =
  'black-sea-eco-monitor.particle-speed';

const PARTICLE_TRAIL_STORAGE_KEY =
  'black-sea-eco-monitor.particle-trail';

const DRIFT_HORIZON_STORAGE_KEY =
  'black-sea-eco-monitor.drift-horizon';

const DRIFT_PARTICLES_STORAGE_KEY =
  'black-sea-eco-monitor.drift-particles';

const statusDot = document.getElementById('connection-dot');
const connectionLabel = document.getElementById('connection-label');
const updateLabel = document.getElementById('update-label');
const eventCount = document.getElementById('event-count');
const resetFiltersButton = document.getElementById('reset-filters');
const languageButtons = [
  ...document.querySelectorAll('[data-language]'),
];

const currentsToggle = document.getElementById(
  'currents-layer-toggle',
);
const currentsNote = document.getElementById(
  'currents-layer-note',
);
const currentsLongTask = document.getElementById(
  'currents-long-task',
);
const currentsLongTaskElapsed = document.getElementById(
  'currents-long-task-elapsed',
);
const currentsLongTaskMessage = document.getElementById(
  'currents-long-task-message',
);
const currentsArrowSizeSlider = document.getElementById(
  'currents-arrow-size',
);
const currentsArrowSizeValue = document.getElementById(
  'currents-arrow-size-value',
);

const currentDisplayModeInputs = [
  ...document.querySelectorAll(
    'input[name="current-display-mode"]',
  ),
];

const particleControls = document.getElementById(
  'particle-controls',
);

const particleCountSlider = document.getElementById(
  'particle-count',
);

const particleCountValue = document.getElementById(
  'particle-count-value',
);

const particleSpeedSlider = document.getElementById(
  'particle-speed',
);

const particleSpeedValue = document.getElementById(
  'particle-speed-value',
);

const particleTrailSlider = document.getElementById(
  'particle-trail',
);

const particleTrailValue = document.getElementById(
  'particle-trail-value',
);

const driftStatus = document.getElementById(
  'drift-status',
);
const driftLongTask = document.getElementById(
  'drift-long-task',
);
const driftLongTaskElapsed = document.getElementById(
  'drift-long-task-elapsed',
);
const driftLongTaskMessage = document.getElementById(
  'drift-long-task-message',
);
const driftPickPointButton = document.getElementById(
  'drift-pick-point',
);
const driftClearButton = document.getElementById(
  'drift-clear',
);
const driftCoordinate = document.getElementById(
  'drift-coordinate',
);
const driftRunButton = document.getElementById(
  'drift-run',
);
const driftHorizonInputs = [
  ...document.querySelectorAll(
    'input[name="drift-horizon"]',
  ),
];
const driftParticlesSlider = document.getElementById(
  'drift-particles',
);
const driftParticlesValue = document.getElementById(
  'drift-particles-value',
);

const eventPanel = document.getElementById('event-panel');
const eventPanelContent = document.getElementById('event-panel-content');
const closeEventPanelButton = document.getElementById('close-event-panel');

const statusInputs = [
  ...document.querySelectorAll('input[data-status]'),
];

const categoryInputs = [
  ...document.querySelectorAll('input[data-category]'),
];

const timeInputs = [
  ...document.querySelectorAll('input[name="time-window"]'),
];

const eventsById = new Map();
const evidenceCache = new Map();
const evidenceRequests = new Map();

let allEvents = [];
let visibleEvents = [];
let visibleGroups = [];
let groupMarkers = [];
let lastSuccessfulUpdate = null;
let connectionState = 'loading';
let connectionErrorMessage = '';
let currentLanguage = loadStoredLanguage();

let currentsPayload = null;
let currentsLoading = false;
let currentsErrorMessage = '';
let currentsPopup = null;

let currentArrowSizePercent =
  normalizeCurrentArrowSizePercent(
    window.localStorage.getItem(
      CURRENT_ARROW_SIZE_STORAGE_KEY,
    ),
    100,
  );

let currentDisplayMode =
  normalizeCurrentDisplayMode(
    window.localStorage.getItem(
      CURRENT_DISPLAY_MODE_STORAGE_KEY,
    ),
    'arrows',
  );

let particleCount =
  normalizeParticleCount(
    window.localStorage.getItem(
      PARTICLE_COUNT_STORAGE_KEY,
    ),
    (
      navigator.hardwareConcurrency
      && navigator.hardwareConcurrency <= 4
    )
      ? 900
      : (
        navigator.hardwareConcurrency
        && navigator.hardwareConcurrency <= 8
      )
        ? 1500
        : 2200,
  );

let particleSpeedPercent =
  normalizeParticleSpeedPercent(
    window.localStorage.getItem(
      PARTICLE_SPEED_STORAGE_KEY,
    ),
    100,
  );

let particleTrailPercent =
  normalizeParticleTrailPercent(
    window.localStorage.getItem(
      PARTICLE_TRAIL_STORAGE_KEY,
    ),
    70,
  );

let currentParticleEngine = null;
let mapIsMoving = false;

let driftSelectionActive = false;
let driftSelectionJustConsumed = false;
let driftSeed = null;
let driftPayload = null;
let driftLoading = false;
let driftErrorMessage = '';

let currentsLoadingStartedAt = null;
let driftLoadingStartedAt = null;
let longTaskTicker = null;

let driftHorizon = normalizeDriftHorizon(
  window.localStorage.getItem(
    DRIFT_HORIZON_STORAGE_KEY,
  ),
  DEFAULT_DRIFT_HORIZON,
);

let driftParticles = normalizeDriftParticles(
  window.localStorage.getItem(
    DRIFT_PARTICLES_STORAGE_KEY,
  ),
  DEFAULT_DRIFT_PARTICLES,
);

let selectedEventId = null;
let selectedGroupId = null;
let panelRenderToken = 0;

const map = new maplibregl.Map({
  container: 'map',
  center: BLACK_SEA_CENTER,
  zoom: BLACK_SEA_INITIAL_ZOOM,
  minZoom: BLACK_SEA_MIN_ZOOM,
  maxZoom: BLACK_SEA_MAX_ZOOM,
  maxBounds: BLACK_SEA_NAVIGATION_BOUNDS,
  renderWorldCopies: false,
  attributionControl: false,
  style: {
    version: 8,
    sources: {
      osm: {
        type: 'raster',
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors',
      },
    },
    layers: [
      { id: 'osm', type: 'raster', source: 'osm' },
    ],
  },
});

map.addControl(
  new maplibregl.NavigationControl({
    visualizePitch: true,
  }),
  'bottom-right',
);

map.addControl(
  new maplibregl.AttributionControl({
    compact: true,
  }),
  'bottom-right',
);

function renderConnectionState() {
  statusDot.className = `status-dot status-dot--${connectionState}`;

  if (connectionState === 'ok') {
    connectionLabel.textContent = t(
      currentLanguage,
      'connection.online',
    );
    updateLabel.textContent = t(
      currentLanguage,
      'connection.updated',
      {
        time: lastSuccessfulUpdate
          ? formatClock(lastSuccessfulUpdate)
          : '—',
      },
    );
    return;
  }

  if (connectionState === 'warning') {
    connectionLabel.textContent = t(
      currentLanguage,
      'connection.offline',
    );
    updateLabel.textContent = t(
      currentLanguage,
      'connection.lastKnown',
      {
        time: lastSuccessfulUpdate
          ? formatClock(lastSuccessfulUpdate)
          : '—',
      },
    );
    return;
  }

  if (connectionState === 'error') {
    connectionLabel.textContent = t(
      currentLanguage,
      'connection.unavailable',
    );
    updateLabel.textContent =
      connectionErrorMessage
      || t(currentLanguage, 'connection.waiting');
    return;
  }

  connectionLabel.textContent = t(
    currentLanguage,
    'connection.connecting',
  );
  updateLabel.textContent = t(
    currentLanguage,
    'connection.waiting',
  );
}

function setConnectionState(
  state,
  errorMessage = '',
) {
  connectionState = state;
  connectionErrorMessage = errorMessage;
  renderConnectionState();
}

function formatClock(date) {
  return date.toLocaleTimeString(
    localeForLanguage(currentLanguage),
    {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    },
  );
}

function readFilterState() {
  const statuses = statusInputs
    .filter((input) => input.checked)
    .map((input) => input.dataset.status);

  const categories = categoryInputs
    .filter((input) => input.checked)
    .map((input) => input.dataset.category);

  const activeTimeInput = timeInputs.find((input) => input.checked);

  return {
    statuses,
    categories,
    days: activeTimeInput?.value ?? '7',
  };
}

function updateEventCount() {
  eventCount.textContent = formatEventCount(
    visibleEvents.length,
    allEvents.length,
    currentLanguage,
  );
}

function getVisibleGroup(groupId) {
  return visibleGroups.find(
    (group) => group.id === groupId,
  ) ?? null;
}

function selectedEventIsVisible() {
  if (!selectedEventId) return false;

  return visibleEvents.some(
    (event) => event.id === selectedEventId,
  );
}

function updateSelectedCircle() {
  if (!map.getLayer('monitor-events-selected')) return;

  map.setFilter(
    'monitor-events-selected',
    [
      '==',
      ['get', 'id'],
      selectedEventId || '__none__',
    ],
  );
}

function updateSelectedGroupMarker() {
  for (const item of groupMarkers) {
    item.element.classList.toggle(
      'colocated-marker--selected',
      item.groupId === selectedGroupId,
    );
  }
}

function clearGroupMarkers() {
  for (const item of groupMarkers) {
    item.marker.remove();
  }

  groupMarkers = [];
}

function createGroupMarker(group) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'colocated-marker';
  button.setAttribute(
    'aria-label',
    t(
      currentLanguage,
      'map.groupAria',
      {
        count: group.count,
        location: localizeLocationName(
          group.locationName,
          currentLanguage,
        ),
      },
    ),
  );

  const count = document.createElement('span');
  count.className = 'colocated-marker__count';
  count.textContent = String(group.count);

  const caption = document.createElement('span');
  caption.className = 'colocated-marker__caption';
  caption.textContent = t(
    currentLanguage,
    'map.incidentsShort',
  );

  button.append(count, caption);

  button.addEventListener('click', (event) => {
    event.preventDefault();
    event.stopPropagation();
    selectGroup(group);
  });

  const marker = new maplibregl.Marker({
    element: button,
    anchor: 'center',
  })
    .setLngLat([
      group.longitude,
      group.latitude,
    ])
    .addTo(map);

  return {
    groupId: group.id,
    marker,
    element: button,
  };
}

function syncGroupMarkers() {
  clearGroupMarkers();

  for (const group of visibleGroups) {
    if (!group.isGroup) continue;

    groupMarkers.push(
      createGroupMarker(group),
    );
  }

  updateSelectedGroupMarker();
}

function reconcileSelectionAfterFilters() {
  if (selectedEventId) {
    if (!selectedEventIsVisible()) {
      clearSelection();
      return;
    }

    const group = findGroupForEvent(
      visibleGroups,
      selectedEventId,
    );

    selectedGroupId = group?.isGroup
      ? group.id
      : null;

    return;
  }

  if (
    selectedGroupId
    && !getVisibleGroup(selectedGroupId)?.isGroup
  ) {
    clearSelection();
  }
}

function refreshSelectedPanel() {
  if (selectedEventId && selectedEventIsVisible()) {
    const event = eventsById.get(selectedEventId);

    if (event) {
      renderEventPanel(
        event,
        selectedGroupId,
      );
    }

    return;
  }

  if (selectedGroupId) {
    const group = getVisibleGroup(selectedGroupId);

    if (group?.isGroup) {
      renderGroupPanel(group);
    }
  }
}

function applyFilters() {
  visibleEvents = filterEvents(
    allEvents,
    readFilterState(),
  );

  visibleGroups = groupCoLocatedEvents(
    visibleEvents,
  );

  reconcileSelectionAfterFilters();

  const singleEvents = visibleGroups
    .filter((group) => !group.isGroup)
    .map((group) => group.events[0]);

  const source = map.getSource('monitor-events');

  if (source) {
    source.setData(
      eventsToFeatureCollection(singleEvents),
    );
  }

  syncGroupMarkers();
  updateSelectedCircle();
  updateEventCount();
  refreshSelectedPanel();
}

function resetFilters() {
  for (const input of statusInputs) input.checked = true;
  for (const input of categoryInputs) input.checked = true;

  for (const input of timeInputs) {
    input.checked = input.value === '7';
  }

  applyFilters();
}

for (const input of [
  ...statusInputs,
  ...categoryInputs,
  ...timeInputs,
]) {
  input.addEventListener('change', applyFilters);
}

resetFiltersButton.addEventListener('click', resetFilters);

function makeElement(tag, className, text) {
  const element = document.createElement(tag);

  if (className) {
    element.className = className;
  }

  if (text !== undefined) {
    element.textContent = text;
  }

  return element;
}

function makeMetric(label, value) {
  const metric = makeElement('div', 'detail-metric');
  const key = makeElement('div', 'detail-metric__label', label);
  const val = makeElement('div', 'detail-metric__value', value);

  metric.append(key, val);
  return metric;
}

function makeStatusPill(label, kind) {
  return makeElement(
    'span',
    `status-pill status-pill--${kind}`,
    label,
  );
}

function renderEvidenceRows(container, rows) {
  container.replaceChildren();

  if (!rows.length) {
    container.append(
      makeElement(
        'div',
        'evidence-empty',
        t(currentLanguage, 'panel.noEvidence'),
      ),
    );
    return;
  }

  for (const evidence of rows) {
    const item = makeElement('article', 'detail-evidence');

    const title = makeElement(
      'div',
      'detail-evidence__title',
      evidence.title
        || t(currentLanguage, 'panel.untitledSource'),
    );

    const meta = makeElement(
      'div',
      'detail-evidence__meta',
      [
        evidence.source
          || t(currentLanguage, 'panel.unknownSource'),
        formatEventDate(
          evidence.published_at,
          currentLanguage,
        ),
      ].join(' · '),
    );

    item.append(title, meta);

    const safeUrl = safeExternalHttpUrl(evidence.url);

    if (safeUrl) {
      const link = makeElement(
        'a',
        'detail-evidence__link',
        t(currentLanguage, 'panel.openSource'),
      );

      link.href = safeUrl;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';

      item.append(link);
    }

    container.append(item);
  }
}

function loadEvidence(eventId) {
  if (evidenceCache.has(eventId)) {
    return Promise.resolve(
      evidenceCache.get(eventId),
    );
  }

  if (evidenceRequests.has(eventId)) {
    return evidenceRequests.get(eventId);
  }

  const request = fetchEventEvidence(eventId)
    .then((rows) => {
      evidenceCache.set(eventId, rows);
      return rows;
    })
    .finally(() => {
      evidenceRequests.delete(eventId);
    });

  evidenceRequests.set(eventId, request);
  return request;
}

function makeBackToGroupButton(group) {
  const button = makeElement(
    'button',
    'detail-back',
    t(
      currentLanguage,
      'group.back',
      { count: formatEventCount(group.count, group.count, currentLanguage) },
    ),
  );

  button.type = 'button';

  button.addEventListener('click', () => {
    selectGroup(group);
  });

  return button;
}

function renderEventPanel(event, originGroupId = null) {
  const token = ++panelRenderToken;
  const vm = eventDetailsViewModel(event, currentLanguage);

  eventPanelContent.replaceChildren();

  const originGroup = originGroupId
    ? getVisibleGroup(originGroupId)
    : null;

  if (originGroup?.isGroup) {
    eventPanelContent.append(
      makeBackToGroupButton(originGroup),
    );
  }

  const header = makeElement('div', 'detail-header');

  const category = makeElement(
    'div',
    'detail-category',
    vm.category,
  );

  category.style.setProperty(
    '--event-color',
    vm.color,
  );

  const location = makeElement(
    'h2',
    'detail-location',
    vm.location,
  );

  const headline = makeElement(
    'div',
    'detail-headline',
    vm.headline,
  );

  header.append(
    category,
    location,
    headline,
  );

  const pills = makeElement(
    'div',
    'detail-pills',
  );

  pills.append(
    makeStatusPill(
      vm.status,
      String(event.status || 'unknown').toLowerCase(),
    ),
    makeStatusPill(
      vm.severity,
      'severity',
    ),
  );

  const metrics = makeElement(
    'div',
    'detail-metrics',
  );

  metrics.append(
    makeMetric(
      t(currentLanguage, 'panel.eventConfidence'),
      vm.confidence,
    ),
    makeMetric(
      t(currentLanguage, 'panel.locationConfidence'),
      vm.locationConfidence,
    ),
    makeMetric(
      t(currentLanguage, 'panel.evidence'),
      String(vm.evidenceCount),
    ),
    makeMetric(
      t(currentLanguage, 'panel.coordinates'),
      vm.coordinates,
    ),
  );

  const locationQuality = makeElement(
    'section',
    'detail-section',
  );

  locationQuality.append(
    makeElement(
      'div',
      'detail-section__title',
      t(currentLanguage, 'panel.locationQuality'),
    ),
  );

  const locationQualityGrid = makeElement(
    'div',
    'detail-quality-grid',
  );

  locationQualityGrid.append(
    makeMetric(
      t(currentLanguage, 'panel.locationType'),
      vm.locationType,
    ),
    makeMetric(
      t(currentLanguage, 'panel.mapScope'),
      vm.locationScope,
    ),
    makeMetric(
      t(currentLanguage, 'panel.coordinateSource'),
      vm.coordinateSource,
    ),
  );

  const qualityNote = makeElement(
    'div',
    'detail-quality-note',
    vm.coordinateInterpretation,
  );

  locationQuality.append(
    locationQualityGrid,
    qualityNote,
  );

  const timeline = makeElement(
    'section',
    'detail-section',
  );

  timeline.append(
    makeElement(
      'div',
      'detail-section__title',
      t(currentLanguage, 'panel.timeline'),
    ),
  );

  const timelineGrid = makeElement(
    'div',
    'detail-timeline',
  );

  timelineGrid.append(
    makeMetric(
      t(currentLanguage, 'panel.incidentTime'),
      vm.incidentTime,
    ),
    makeMetric(
      t(currentLanguage, 'panel.sourceTime'),
      vm.sourceTime,
    ),
    makeMetric(
      t(currentLanguage, 'panel.detected'),
      vm.detectionTime,
    ),
    makeMetric(
      t(currentLanguage, 'panel.firstSeen'),
      vm.firstSeen,
    ),
    makeMetric(
      t(currentLanguage, 'panel.latest'),
      vm.lastSeen,
    ),
  );

  timeline.append(timelineGrid);

  const evidenceSection = makeElement(
    'section',
    'detail-section',
  );

  const evidenceHeading = makeElement(
    'div',
    'detail-section__title',
    t(
      currentLanguage,
      'panel.evidenceHeading',
      { count: vm.evidenceCount },
    ),
  );

  const evidenceList = makeElement(
    'div',
    'detail-evidence-list',
  );

  evidenceList.append(
    makeElement(
      'div',
      'evidence-loading',
      t(currentLanguage, 'panel.loadingSources'),
    ),
  );

  evidenceSection.append(
    evidenceHeading,
    evidenceList,
  );

  eventPanelContent.append(
    header,
    pills,
    metrics,
    locationQuality,
    timeline,
    evidenceSection,
  );

  eventPanel.classList.add(
    'event-panel--open',
  );

  eventPanel.setAttribute(
    'aria-hidden',
    'false',
  );

  loadEvidence(event.id)
    .then((rows) => {
      if (
        token !== panelRenderToken
        || selectedEventId !== event.id
      ) {
        return;
      }

      renderEvidenceRows(
        evidenceList,
        rows,
      );
    })
    .catch((error) => {
      if (
        token !== panelRenderToken
        || selectedEventId !== event.id
      ) {
        return;
      }

      evidenceList.replaceChildren(
        makeElement(
          'div',
          'evidence-error',
          t(
            currentLanguage,
            'panel.evidenceUnavailable',
            { message: error.message },
          ),
        ),
      );
    });
}

function makeGroupEventCard(event, group) {
  const vm = eventDetailsViewModel(event, currentLanguage);

  const card = makeElement(
    'button',
    'group-event-card',
  );

  card.type = 'button';

  const top = makeElement(
    'div',
    'group-event-card__top',
  );

  const category = makeElement(
    'div',
    'group-event-card__category',
    vm.category,
  );

  category.style.setProperty(
    '--event-color',
    vm.color,
  );

  const status = makeElement(
    'span',
    'group-event-card__status',
    vm.status,
  );

  top.append(category, status);

  const title = makeElement(
    'div',
    'group-event-card__title',
    vm.headline,
  );

  const meta = makeElement(
    'div',
    'group-event-card__meta',
    t(
      currentLanguage,
      'group.cardMeta',
      {
        severity: vm.severity,
        confidence: vm.confidence,
        evidence: vm.evidenceCount,
      },
    ),
  );

  card.append(top, title, meta);

  card.addEventListener('click', () => {
    selectEvent(event, group.id);
  });

  return card;
}

function renderGroupPanel(group) {
  panelRenderToken += 1;
  eventPanelContent.replaceChildren();

  const header = makeElement(
    'div',
    'group-detail-header',
  );

  const kicker = makeElement(
    'div',
    'group-detail-kicker',
    t(currentLanguage, 'group.kicker'),
  );

  const location = makeElement(
    'h2',
    'detail-location',
    localizeLocationName(
      group.locationName,
      currentLanguage,
    ),
  );

  const summary = makeElement(
    'div',
    'detail-headline',
    t(
      currentLanguage,
      'group.summary',
      {
        count: formatEventCount(
          group.count,
          group.count,
          currentLanguage,
        ),
      },
    ),
  );

  header.append(
    kicker,
    location,
    summary,
  );

  const coordinate = makeElement(
    'div',
    'group-coordinate',
    `${group.latitude.toFixed(5)}, ${group.longitude.toFixed(5)}`,
  );

  const list = makeElement(
    'div',
    'group-event-list',
  );

  for (const event of group.events) {
    list.append(
      makeGroupEventCard(
        event,
        group,
      ),
    );
  }

  eventPanelContent.append(
    header,
    coordinate,
    list,
  );

  eventPanel.classList.add(
    'event-panel--open',
  );

  eventPanel.setAttribute(
    'aria-hidden',
    'false',
  );
}

function selectEvent(event, originGroupId = null) {
  selectedEventId = event.id;
  selectedGroupId = originGroupId;

  updateSelectedCircle();
  updateSelectedGroupMarker();

  renderEventPanel(
    event,
    originGroupId,
  );
}

function selectGroup(group) {
  selectedEventId = null;
  selectedGroupId = group.id;

  updateSelectedCircle();
  updateSelectedGroupMarker();

  renderGroupPanel(group);
}

function clearSelection() {
  selectedEventId = null;
  selectedGroupId = null;
  panelRenderToken += 1;

  updateSelectedCircle();
  updateSelectedGroupMarker();

  eventPanel.classList.remove(
    'event-panel--open',
  );

  eventPanel.setAttribute(
    'aria-hidden',
    'true',
  );
}

closeEventPanelButton.addEventListener(
  'click',
  clearSelection,
);

document.addEventListener(
  'keydown',
  (event) => {
    if (
      event.key === 'Escape'
      && (selectedEventId || selectedGroupId)
    ) {
      clearSelection();
    }
  },
);


function emptyFeatureCollection() {
  return {
    type: 'FeatureCollection',
    features: [],
  };
}



function setGeoJSONSourceData(
  sourceId,
  data,
) {
  const source = map.getSource(sourceId);

  if (source) {
    source.setData(data);
  }
}


function renderLongTaskUX() {
  const now = Date.now();

  const currentsView = longTaskViewModel({
    startedAtMs: currentsLoadingStartedAt,
    nowMs: now,
    revealAfterMs: 650,
    slowAfterSeconds: 120,
  });

  if (currentsLongTask) {
    currentsLongTask.hidden = !(
      currentsLoading
      && currentsView.visible
    );
  }

  if (currentsLongTaskElapsed) {
    currentsLongTaskElapsed.textContent = t(
      currentLanguage,
      'task.elapsed',
      { time: currentsView.elapsedText },
    );
  }

  if (currentsLongTaskMessage) {
    currentsLongTaskMessage.textContent = t(
      currentLanguage,
      currentsView.slow
        ? 'ocean.waitSlow'
        : 'ocean.waitNormal',
    );
  }

  const driftView = longTaskViewModel({
    startedAtMs: driftLoadingStartedAt,
    nowMs: now,
    revealAfterMs: 450,
    slowAfterSeconds: 180,
  });

  if (driftLongTask) {
    driftLongTask.hidden = !(
      driftLoading
      && driftView.visible
    );
  }

  if (driftLongTaskElapsed) {
    driftLongTaskElapsed.textContent = t(
      currentLanguage,
      'task.elapsed',
      { time: driftView.elapsedText },
    );
  }

  if (driftLongTaskMessage) {
    driftLongTaskMessage.textContent = t(
      currentLanguage,
      driftView.slow
        ? 'drift.waitSlow'
        : 'drift.waitNormal',
    );
  }
}


function syncLongTaskTicker() {
  const anyActive = Boolean(
    currentsLoadingStartedAt
    || driftLoadingStartedAt
  );

  if (anyActive && longTaskTicker === null) {
    longTaskTicker = window.setInterval(
      renderLongTaskUX,
      1000,
    );
  }

  if (!anyActive && longTaskTicker !== null) {
    window.clearInterval(longTaskTicker);
    longTaskTicker = null;
  }

  renderLongTaskUX();
}


function startLongTask(kind) {
  if (kind === 'currents') {
    currentsLoadingStartedAt = Date.now();
  }

  if (kind === 'drift') {
    driftLoadingStartedAt = Date.now();
  }

  syncLongTaskTicker();
}


function stopLongTask(kind) {
  if (kind === 'currents') {
    currentsLoadingStartedAt = null;
  }

  if (kind === 'drift') {
    driftLoadingStartedAt = null;
  }

  syncLongTaskTicker();
}


function renderDriftControls() {
  for (const input of driftHorizonInputs) {
    input.checked = Number(input.value) === driftHorizon;
  }

  if (driftParticlesSlider) {
    driftParticlesSlider.value = String(driftParticles);
  }

  if (driftParticlesValue) {
    driftParticlesValue.textContent = String(driftParticles);
  }

  if (driftCoordinate) {
    driftCoordinate.textContent = driftSeed
      ? `${driftSeed.latitude.toFixed(5)}, ${driftSeed.longitude.toFixed(5)}`
      : '—';
  }

  if (driftRunButton) {
    driftRunButton.disabled = !driftSeed || driftLoading;
    driftRunButton.textContent = t(
      currentLanguage,
      driftLoading
        ? 'drift.runningButton'
        : (driftPayload ? 'drift.rerun' : 'drift.run'),
    );
  }

  for (const input of driftHorizonInputs) {
    input.disabled = driftLoading;
  }

  if (driftParticlesSlider) {
    driftParticlesSlider.disabled = driftLoading;
  }

  if (driftPickPointButton) {
    driftPickPointButton.disabled = driftLoading;
  }

  if (driftClearButton) {
    driftClearButton.disabled = driftLoading;
  }

  driftStatus
    ?.closest('.drift-control')
    ?.classList.toggle(
      'drift-control--busy',
      driftLoading,
    );

  if (driftPickPointButton) {
    driftPickPointButton.classList.toggle(
      'drift-button--active',
      driftSelectionActive,
    );
    driftPickPointButton.textContent = t(
      currentLanguage,
      driftSelectionActive
        ? 'drift.pickPointActive'
        : 'drift.pickPoint',
    );
  }

  if (driftStatus) {
    driftStatus.classList.toggle(
      'drift-control__status--loading',
      driftLoading,
    );
    driftStatus.classList.toggle(
      'drift-control__status--ready',
      Boolean(driftPayload) && !driftLoading && !driftErrorMessage,
    );
    driftStatus.classList.toggle(
      'drift-control__status--error',
      Boolean(driftErrorMessage),
    );

    if (driftLoading) {
      driftStatus.textContent = t(currentLanguage, 'drift.loading');
    } else if (driftErrorMessage) {
      driftStatus.textContent = t(
        currentLanguage,
        'drift.error',
        { message: driftErrorMessage },
      );
    } else if (driftPayload) {
      const snapshot = snapshotForHorizon(
        driftPayload,
        driftHorizon,
      );

      driftStatus.textContent = t(
        currentLanguage,
        'drift.ready',
        {
          hours: driftHorizon,
          count: snapshot?.particle_count ?? driftParticles,
        },
      );
    } else if (driftSelectionActive) {
      driftStatus.textContent = t(currentLanguage, 'drift.selecting');
    } else if (driftSeed) {
      driftStatus.textContent = t(currentLanguage, 'drift.pointSelected');
    } else {
      driftStatus.textContent = t(currentLanguage, 'drift.help');
    }
  }

  renderLongTaskUX();
}


function clearDriftMapData({ keepSeed = false } = {}) {
  setGeoJSONSourceData(
    'drift-cloud',
    { type: 'FeatureCollection', features: [] },
  );
  setGeoJSONSourceData(
    'drift-envelope',
    { type: 'FeatureCollection', features: [] },
  );
  setGeoJSONSourceData(
    'drift-track',
    { type: 'FeatureCollection', features: [] },
  );
  setGeoJSONSourceData(
    'drift-center',
    { type: 'FeatureCollection', features: [] },
  );

  if (!keepSeed) {
    setGeoJSONSourceData(
      'drift-seed',
      { type: 'FeatureCollection', features: [] },
    );
  }
}


function renderDriftMap() {
  setGeoJSONSourceData(
    'drift-seed',
    driftSeedGeoJSON(driftSeed),
  );

  if (!driftPayload) {
    clearDriftMapData({ keepSeed: true });
    return;
  }

  const snapshot = snapshotForHorizon(
    driftPayload,
    driftHorizon,
  );

  if (!snapshot) {
    clearDriftMapData({ keepSeed: true });
    return;
  }

  setGeoJSONSourceData(
    'drift-cloud',
    driftPointsGeoJSON(snapshot),
  );
  setGeoJSONSourceData(
    'drift-envelope',
    driftEnvelopeGeoJSON(snapshot),
  );
  setGeoJSONSourceData(
    'drift-center',
    driftCenterGeoJSON(snapshot),
  );
  setGeoJSONSourceData(
    'drift-track',
    driftTrackGeoJSON(
      driftPayload,
      driftHorizon,
    ),
  );
}


function clearDriftForecast() {
  driftSelectionActive = false;
  driftSeed = null;
  driftPayload = null;
  driftLoading = false;
  driftErrorMessage = '';
  stopLongTask('drift');
  map.getCanvas().style.cursor = '';
  clearDriftMapData();
  renderDriftControls();
}


async function runDriftForecast() {
  if (!driftSeed || driftLoading) {
    return;
  }

  driftLoading = true;
  driftErrorMessage = '';
  startLongTask('drift');
  renderDriftControls();

  try {
    const payload = await fetchDriftForecast({
      longitude: driftSeed.longitude,
      latitude: driftSeed.latitude,
      hours: driftHorizon,
      particles: driftParticles,
    });

    driftPayload = payload;
    renderDriftMap();
  } catch (error) {
    console.error('[Black Sea Eco Monitor drift]', error);
    driftPayload = null;
    driftErrorMessage = error?.message || String(error);
    clearDriftMapData({ keepSeed: true });
  } finally {
    driftLoading = false;
    stopLongTask('drift');
    renderDriftControls();
  }
}


function installDriftLayer() {
  const empty = {
    type: 'FeatureCollection',
    features: [],
  };

  for (const sourceId of [
    'drift-envelope',
    'drift-track',
    'drift-cloud',
    'drift-seed',
    'drift-center',
  ]) {
    map.addSource(sourceId, {
      type: 'geojson',
      data: empty,
    });
  }

  map.addLayer({
    id: 'drift-envelope-fill',
    type: 'fill',
    source: 'drift-envelope',
    paint: {
      'fill-color': '#ff8a00',
      'fill-opacity': 0.13,
    },
  });

  map.addLayer({
    id: 'drift-envelope-line',
    type: 'line',
    source: 'drift-envelope',
    paint: {
      'line-color': '#ff9f43',
      'line-width': 2,
      'line-opacity': 0.88,
    },
  });

  map.addLayer({
    id: 'drift-track-line',
    type: 'line',
    source: 'drift-track',
    paint: {
      'line-color': '#ffd60a',
      'line-width': 2.2,
      'line-opacity': 0.92,
      'line-dasharray': [2, 1.5],
    },
  });

  map.addLayer({
    id: 'drift-cloud-points',
    type: 'circle',
    source: 'drift-cloud',
    paint: {
      'circle-radius': [
        'interpolate',
        ['linear'],
        ['zoom'],
        3, 2.0,
        8, 3.6,
      ],
      'circle-color': '#ff6b35',
      'circle-opacity': 0.48,
      'circle-stroke-color': '#ffd166',
      'circle-stroke-width': 0.5,
      'circle-stroke-opacity': 0.55,
    },
  });

  map.addLayer({
    id: 'drift-seed-point',
    type: 'circle',
    source: 'drift-seed',
    paint: {
      'circle-radius': 7,
      'circle-color': '#071018',
      'circle-stroke-color': '#ffffff',
      'circle-stroke-width': 2.5,
    },
  });

  map.addLayer({
    id: 'drift-center-point',
    type: 'circle',
    source: 'drift-center',
    paint: {
      'circle-radius': 6,
      'circle-color': '#ffd60a',
      'circle-stroke-color': '#111827',
      'circle-stroke-width': 2,
    },
  });
}


function renderCurrentArrowSizeControl() {
  if (currentsArrowSizeSlider) {
    currentsArrowSizeSlider.value = String(
      currentArrowSizePercent,
    );
  }

  if (currentsArrowSizeValue) {
    currentsArrowSizeValue.textContent =
      `${currentArrowSizePercent}%`;
  }
}


function modeShowsArrows() {
  return (
    currentDisplayMode === 'arrows'
    || currentDisplayMode === 'both'
  );
}


function modeShowsParticles() {
  return (
    currentDisplayMode === 'particles'
    || currentDisplayMode === 'both'
  );
}


function renderCurrentDisplayControls() {
  for (
    const input
    of currentDisplayModeInputs
  ) {
    input.checked =
      input.value
      === currentDisplayMode;
  }

  if (particleCountSlider) {
    particleCountSlider.value =
      String(particleCount);
  }

  if (particleCountValue) {
    particleCountValue.textContent =
      String(particleCount);
  }

  if (particleSpeedSlider) {
    particleSpeedSlider.value =
      String(
        particleSpeedPercent,
      );
  }

  if (particleSpeedValue) {
    particleSpeedValue.textContent =
      `${particleSpeedPercent}%`;
  }

  if (particleTrailSlider) {
    particleTrailSlider.value =
      String(
        particleTrailPercent,
      );
  }

  if (particleTrailValue) {
    particleTrailValue.textContent =
      `${particleTrailPercent}%`;
  }

  const particlesEnabled =
    modeShowsParticles();

  particleControls?.classList.toggle(
    'particle-controls--disabled',
    !particlesEnabled,
  );

  for (
    const input
    of [
      particleCountSlider,
      particleSpeedSlider,
      particleTrailSlider,
    ]
  ) {
    if (input) {
      input.disabled =
        !particlesEnabled;
    }
  }

  const arrowControl =
    currentsArrowSizeSlider
      ?.closest(
        '.current-size-control',
      );

  arrowControl?.classList.toggle(
    'current-size-control--disabled',
    !modeShowsArrows(),
  );

  if (currentsArrowSizeSlider) {
    currentsArrowSizeSlider.disabled =
      !modeShowsArrows();
  }
}


function ensureParticleEngine() {
  if (currentParticleEngine) {
    return currentParticleEngine;
  }

  const mapCanvasContainer =
    map.getCanvasContainer();

  const canvas =
    document.createElement('canvas');

  canvas.id =
    'current-particles-canvas';

  canvas.className =
    'current-particles-canvas';

  canvas.setAttribute(
    'aria-hidden',
    'true',
  );

  mapCanvasContainer.append(
    canvas,
  );

  currentParticleEngine =
    new CurrentParticleEngine({
      canvas,
      map,
      particleCount,
      speedPercent:
        particleSpeedPercent,
      trailPercent:
        particleTrailPercent,
    });

  if (currentsPayload) {
    currentParticleEngine.setField(
      currentsPayload,
    );
  }

  return currentParticleEngine;
}


function syncCurrentVisualization() {
  renderCurrentDisplayControls();

  const layerEnabled =
    currentLayerVisible();

  const arrowVisibility =
    (
      layerEnabled
      && modeShowsArrows()
    )
      ? 'visible'
      : 'none';

  for (const layerId of [
    'ocean-currents-points',
    'ocean-currents-arrows',
  ]) {
    if (map.getLayer(layerId)) {
      map.setLayoutProperty(
        layerId,
        'visibility',
        arrowVisibility,
      );
    }
  }

  if (
    !layerEnabled
    || !modeShowsParticles()
    || !currentsPayload
    || document.hidden
    || mapIsMoving
  ) {
    currentParticleEngine?.stop();
  } else {
    const engine =
      ensureParticleEngine();

    engine.setParticleCount(
      particleCount,
    );

    engine.setSpeedPercent(
      particleSpeedPercent,
    );

    engine.setTrailPercent(
      particleTrailPercent,
    );

    engine.start();
  }

  if (
    !layerEnabled
    && currentsPopup
  ) {
    currentsPopup.remove();
    currentsPopup = null;
  }
}


function applyCurrentArrowSize() {
  renderCurrentArrowSizeControl();

  if (!map.getLayer('ocean-currents-arrows')) {
    return;
  }

  map.setLayoutProperty(
    'ocean-currents-arrows',
    'icon-size',
    currentArrowSizeExpression(
      currentArrowSizePercent,
    ),
  );
}


currentsArrowSizeSlider?.addEventListener(
  'input',
  () => {
    currentArrowSizePercent =
      normalizeCurrentArrowSizePercent(
        currentsArrowSizeSlider.value,
      );

    window.localStorage.setItem(
      CURRENT_ARROW_SIZE_STORAGE_KEY,
      String(currentArrowSizePercent),
    );

    applyCurrentArrowSize();
  },
);


renderCurrentArrowSizeControl();


for (
  const input
  of currentDisplayModeInputs
) {
  input.addEventListener(
    'change',
    () => {
      if (!input.checked) {
        return;
      }

      currentDisplayMode =
        normalizeCurrentDisplayMode(
          input.value,
        );

      window.localStorage.setItem(
        CURRENT_DISPLAY_MODE_STORAGE_KEY,
        currentDisplayMode,
      );

      syncCurrentVisualization();
    },
  );
}


particleCountSlider?.addEventListener(
  'input',
  () => {
    particleCount =
      normalizeParticleCount(
        particleCountSlider.value,
      );

    window.localStorage.setItem(
      PARTICLE_COUNT_STORAGE_KEY,
      String(particleCount),
    );

    currentParticleEngine?.setParticleCount(
      particleCount,
    );

    renderCurrentDisplayControls();
  },
);


particleSpeedSlider?.addEventListener(
  'input',
  () => {
    particleSpeedPercent =
      normalizeParticleSpeedPercent(
        particleSpeedSlider.value,
      );

    window.localStorage.setItem(
      PARTICLE_SPEED_STORAGE_KEY,
      String(
        particleSpeedPercent,
      ),
    );

    currentParticleEngine?.setSpeedPercent(
      particleSpeedPercent,
    );

    renderCurrentDisplayControls();
  },
);


particleTrailSlider?.addEventListener(
  'input',
  () => {
    particleTrailPercent =
      normalizeParticleTrailPercent(
        particleTrailSlider.value,
      );

    window.localStorage.setItem(
      PARTICLE_TRAIL_STORAGE_KEY,
      String(
        particleTrailPercent,
      ),
    );

    currentParticleEngine?.setTrailPercent(
      particleTrailPercent,
    );

    renderCurrentDisplayControls();
  },
);


renderCurrentDisplayControls();


for (const input of driftHorizonInputs) {
  input.addEventListener('change', () => {
    if (!input.checked) return;

    driftHorizon = normalizeDriftHorizon(input.value);
    window.localStorage.setItem(
      DRIFT_HORIZON_STORAGE_KEY,
      String(driftHorizon),
    );

    // An existing response can contain lower cumulative horizons.
    // If the chosen horizon is already available, redraw immediately;
    // otherwise the Run button triggers a new backend simulation.
    if (snapshotForHorizon(driftPayload, driftHorizon)) {
      renderDriftMap();
    } else if (driftPayload) {
      driftPayload = null;
      clearDriftMapData({ keepSeed: true });
    }

    renderDriftControls();
  });
}


driftParticlesSlider?.addEventListener('input', () => {
  driftParticles = normalizeDriftParticles(
    driftParticlesSlider.value,
  );

  window.localStorage.setItem(
    DRIFT_PARTICLES_STORAGE_KEY,
    String(driftParticles),
  );

  renderDriftControls();
});


driftPickPointButton?.addEventListener('click', () => {
  driftSelectionActive = !driftSelectionActive;
  map.getCanvas().style.cursor = driftSelectionActive
    ? 'crosshair'
    : '';
  renderDriftControls();
});


driftClearButton?.addEventListener('click', () => {
  clearDriftForecast();
});


driftRunButton?.addEventListener('click', () => {
  void runDriftForecast();
});


function createCurrentArrowImage() {
  const size = 96;
  const canvas = document.createElement('canvas');
  canvas.width = size;
  canvas.height = size;

  const context = canvas.getContext('2d');

  context.clearRect(0, 0, size, size);

  // Large arrow with a very high-contrast silhouette.
  // Bright warm fill remains readable over blue water,
  // while the dark outline keeps it visible over land,
  // labels and administrative borders.
  context.beginPath();
  context.moveTo(48, 6);
  context.lineTo(82, 38);
  context.lineTo(63, 38);
  context.lineTo(63, 89);
  context.lineTo(33, 89);
  context.lineTo(33, 38);
  context.lineTo(14, 38);
  context.closePath();

  // Soft warm glow.
  context.save();
  context.shadowColor = 'rgba(255, 214, 10, 0.85)';
  context.shadowBlur = 12;
  context.fillStyle = '#ff7a00';
  context.fill();
  context.restore();

  // Dark outer contour.
  context.strokeStyle = 'rgba(17, 24, 39, 0.98)';
  context.lineWidth = 10;
  context.lineJoin = 'round';
  context.stroke();

  // Bright inner fill.
  context.fillStyle = '#ff8a00';
  context.fill();

  // Thin light accent to keep the arrow crisp.
  context.strokeStyle = '#ffe08a';
  context.lineWidth = 3;
  context.stroke();

  return context.getImageData(
    0,
    0,
    size,
    size,
  );
}

function currentLayerVisible() {
  return Boolean(currentsToggle?.checked);
}

function setCurrentLayerVisibility(visible) {
  if (!visible) {
    currentParticleEngine?.stop();
  }

  syncCurrentVisualization();
}

function renderCurrentsStatus() {
  renderLongTaskUX();

  if (!currentsNote) return;

  currentsNote.classList.toggle(
    'ocean-layer-note--loading',
    currentsLoading,
  );
  currentsNote.classList.toggle(
    'ocean-layer-note--error',
    Boolean(currentsErrorMessage),
  );

  if (!currentLayerVisible()) {
    currentsNote.textContent = t(
      currentLanguage,
      'ocean.currentsOff',
    );
    return;
  }

  if (currentsLoading) {
    currentsNote.textContent = t(
      currentLanguage,
      'ocean.currentsLoading',
    );
    return;
  }

  if (currentsErrorMessage) {
    currentsNote.textContent = t(
      currentLanguage,
      'ocean.currentsError',
      {
        message: currentsErrorMessage,
      },
    );
    return;
  }

  if (currentsPayload) {
    const key = currentsPayload.cache?.status
      === 'stale_fallback'
      ? 'ocean.currentsStale'
      : 'ocean.currentsReady';

    currentsNote.textContent = t(
      currentLanguage,
      key,
      {
        time: formatCurrentValidTime(
          currentsPayload.valid_time,
          localeForLanguage(currentLanguage),
        ),
        count: currentsPayload.vector_count,
      },
    );
    return;
  }

  currentsNote.textContent = t(
    currentLanguage,
    'ocean.currentsOff',
  );
}

function makeCurrentPopupContent(properties) {
  const root = document.createElement('div');
  root.className = 'ocean-current-popup';

  const title = document.createElement('div');
  title.className = 'ocean-current-popup__title';
  title.textContent = t(
    currentLanguage,
    'ocean.popupTitle',
  );
  root.append(title);

  const rows = [
    [
      t(currentLanguage, 'ocean.speed'),
      formatCurrentSpeed(properties.speed),
    ],
    [
      t(currentLanguage, 'ocean.direction'),
      `${cardinalDirection(
        properties.direction_deg,
        currentLanguage,
      )} · ${Number(properties.direction_deg).toFixed(0)}°`,
    ],
    [
      t(currentLanguage, 'ocean.components'),
      `u ${Number(properties.u).toFixed(3)} · v ${Number(properties.v).toFixed(3)} m/s`,
    ],
    [
      t(currentLanguage, 'ocean.modelTime'),
      formatCurrentValidTime(
        currentsPayload?.valid_time,
        localeForLanguage(currentLanguage),
      ),
    ],
    [
      t(currentLanguage, 'ocean.depth'),
      currentsPayload?.depth_m == null
        ? '—'
        : `${Number(currentsPayload.depth_m).toFixed(2)} m`,
    ],
    [
      t(currentLanguage, 'ocean.source'),
      currentsPayload?.source || 'Copernicus Marine',
    ],
  ];

  for (const [keyText, valueText] of rows) {
    const row = document.createElement('div');
    row.className = 'ocean-current-popup__row';

    const key = document.createElement('div');
    key.className = 'ocean-current-popup__key';
    key.textContent = keyText;

    const value = document.createElement('div');
    value.className = 'ocean-current-popup__value';
    value.textContent = valueText;

    row.append(key, value);
    root.append(row);
  }

  return root;
}

function installCurrentLayer() {
  if (!map.hasImage('ocean-current-arrow')) {
    map.addImage(
      'ocean-current-arrow',
      createCurrentArrowImage(),
      {
        pixelRatio: 2,
      },
    );
  }

  map.addSource('ocean-currents', {
    type: 'geojson',
    data: emptyFeatureCollection(),
  });

  map.addLayer({
    id: 'ocean-currents-points',
    type: 'circle',
    source: 'ocean-currents',
    layout: {
      visibility: 'none',
    },
    paint: {
      'circle-radius': [
        'interpolate',
        ['linear'],
        ['get', 'speed'],
        0, 2.4,
        0.15, 3.2,
        0.7, 5.2,
      ],
      'circle-color': '#111827',
      'circle-opacity': 0.78,
      'circle-stroke-color': '#ffd60a',
      'circle-stroke-width': 1.5,
      'circle-stroke-opacity': 0.95,
    },
  });

  map.addLayer({
    id: 'ocean-currents-arrows',
    type: 'symbol',
    source: 'ocean-currents',
    layout: {
      visibility: 'none',
      'icon-image': 'ocean-current-arrow',
      'icon-size': currentArrowSizeExpression(
        currentArrowSizePercent,
      ),
      'icon-rotate': ['get', 'direction_deg'],
      'icon-rotation-alignment': 'map',
      'icon-pitch-alignment': 'map',
      'icon-allow-overlap': true,
      'icon-ignore-placement': true,
      'icon-padding': 0,
    },
    paint: {
      'icon-opacity': [
        'interpolate',
        ['linear'],
        ['get', 'speed'],
        0, 0.92,
        0.08, 0.96,
        0.15, 0.98,
        0.7, 1.0,
      ],
    },
  });

  applyCurrentArrowSize();

  map.on(
    'mouseenter',
    'ocean-currents-arrows',
    () => {
      map.getCanvas().style.cursor = 'pointer';
    },
  );

  map.on(
    'mouseleave',
    'ocean-currents-arrows',
    () => {
      map.getCanvas().style.cursor = '';
    },
  );

  map.on(
    'click',
    'ocean-currents-arrows',
    (event) => {
      if (
        driftSelectionActive
        || driftSelectionJustConsumed
      ) return;

      const feature = event.features?.[0];

      if (!feature) return;

      if (currentsPopup) {
        currentsPopup.remove();
      }

      currentsPopup = new maplibregl.Popup({
        closeButton: true,
        closeOnClick: true,
        offset: 10,
      })
        .setLngLat(
          feature.geometry.coordinates,
        )
        .setDOMContent(
          makeCurrentPopupContent(
            feature.properties ?? {},
          ),
        )
        .addTo(map);
    },
  );
}

async function refreshCurrents() {
  if (!currentLayerVisible() || currentsLoading) return;

  currentsLoading = true;
  currentsErrorMessage = '';
  startLongTask('currents');
  renderCurrentsStatus();

  try {
    const payload = await fetchOceanCurrents({
      stride: CURRENTS_STRIDE,
    });

    currentsPayload = payload;

    const source = map.getSource(
      'ocean-currents',
    );

    if (source) {
      source.setData(
        currentsToFeatureCollection(payload),
      );
    }

    if (currentParticleEngine) {
      currentParticleEngine.setField(
        payload,
      );
    }

    setCurrentLayerVisibility(true);
  } catch (error) {
    console.error(
      '[Black Sea Eco Monitor / currents]',
      error,
    );

    currentsErrorMessage = error.message;

    if (!currentsPayload) {
      setCurrentLayerVisibility(false);
    }
  } finally {
    currentsLoading = false;
    stopLongTask('currents');
    renderCurrentsStatus();
  }
}

currentsToggle?.addEventListener(
  'change',
  () => {
    if (currentLayerVisible()) {
      setCurrentLayerVisibility(true);
      void refreshCurrents();
    } else {
      setCurrentLayerVisibility(false);
      renderCurrentsStatus();
    }
  },
);


document.addEventListener(
  'visibilitychange',
  () => {
    syncCurrentVisualization();
  },
);


map.on(
  'movestart',
  () => {
    mapIsMoving = true;
    currentParticleEngine?.stop();
  },
);


map.on(
  'move',
  () => {
    currentParticleEngine?.clear();
  },
);


map.on(
  'moveend',
  () => {
    mapIsMoving = false;
    currentParticleEngine?.resize();
    syncCurrentVisualization();
  },
);


map.on(
  'resize',
  () => {
    currentParticleEngine?.resize();
  },
);


function localizeStaticDom() {
  document.documentElement.lang = currentLanguage;
  document.title = t(
    currentLanguage,
    'site.title',
  );

  const metaDescription = document.getElementById(
    'meta-description',
  );

  if (metaDescription) {
    metaDescription.setAttribute(
      'content',
      t(
        currentLanguage,
        'site.description',
      ),
    );
  }

  for (const element of document.querySelectorAll('[data-i18n]')) {
    element.textContent = t(
      currentLanguage,
      element.dataset.i18n,
    );
  }

  for (const element of document.querySelectorAll('[data-i18n-aria-label]')) {
    element.setAttribute(
      'aria-label',
      t(
        currentLanguage,
        element.dataset.i18nAriaLabel,
      ),
    );
  }

  for (const button of languageButtons) {
    const language = button.dataset.language;
    const selected = language === currentLanguage;

    button.classList.toggle(
      'language-switch__button--active',
      selected,
    );

    button.setAttribute(
      'aria-pressed',
      String(selected),
    );

    button.title = t(
      currentLanguage,
      language === 'ru'
        ? 'language.ru'
        : 'language.en',
    );
  }
}

function localizeMapControls() {
  const controls = [
    [
      '.maplibregl-ctrl-zoom-in',
      'map.zoomIn',
    ],
    [
      '.maplibregl-ctrl-zoom-out',
      'map.zoomOut',
    ],
    [
      '.maplibregl-ctrl-compass',
      'map.resetBearing',
    ],
    [
      '.maplibregl-ctrl-attrib-button',
      'map.attribution',
    ],
  ];

  for (const [selector, key] of controls) {
    const element = document.querySelector(selector);

    if (!element) continue;

    const label = t(currentLanguage, key);
    element.title = label;
    element.setAttribute('aria-label', label);
  }
}

function applyLanguage(language) {
  currentLanguage = saveLanguage(language);

  localizeStaticDom();
  localizeMapControls();
  renderConnectionState();
  updateEventCount();
  syncGroupMarkers();
  refreshSelectedPanel();
  renderCurrentsStatus();
  renderCurrentDisplayControls();
  renderLongTaskUX();
  renderDriftControls();

  if (currentsPopup) {
    currentsPopup.remove();
    currentsPopup = null;
  }
}

for (const button of languageButtons) {
  button.addEventListener('click', () => {
    applyLanguage(
      button.dataset.language,
    );
  });
}

applyLanguage(currentLanguage);

function installEventLayer() {
  map.addSource('monitor-events', {
    type: 'geojson',
    data: eventsToFeatureCollection([]),
  });

  map.addLayer({
    id: 'monitor-events-glow',
    type: 'circle',
    source: 'monitor-events',
    paint: {
      'circle-radius': 16,
      'circle-color': ['get', 'markerColor'],
      'circle-opacity': 0.16,
      'circle-blur': 0.7,
    },
  });

  map.addLayer({
    id: 'monitor-events-selected',
    type: 'circle',
    source: 'monitor-events',
    filter: [
      '==',
      ['get', 'id'],
      '__none__',
    ],
    paint: {
      'circle-radius': [
        'interpolate',
        ['linear'],
        ['zoom'],
        3, 15,
        8, 22,
      ],
      'circle-color': ['get', 'markerColor'],
      'circle-opacity': 0.18,
      'circle-stroke-width': 3,
      'circle-stroke-color': '#ffffff',
      'circle-blur': 0.18,
    },
  });

  map.addLayer({
    id: 'monitor-events',
    type: 'circle',
    source: 'monitor-events',
    paint: {
      'circle-radius': [
        'interpolate',
        ['linear'],
        ['zoom'],
        3, 6,
        8, 11,
      ],
      'circle-color': ['get', 'markerColor'],
      'circle-stroke-width': 2,
      'circle-stroke-color': '#ffffff',
      'circle-opacity': 0.95,
    },
  });

  map.on('mouseenter', 'monitor-events', () => {
    map.getCanvas().style.cursor = 'pointer';
  });

  map.on('mouseleave', 'monitor-events', () => {
    map.getCanvas().style.cursor = '';
  });

  map.on('click', 'monitor-events', (event) => {
    if (
      driftSelectionActive
      || driftSelectionJustConsumed
    ) return;

    const feature = event.features?.[0];
    const eventId = feature?.properties?.id;
    const monitorEvent = eventsById.get(eventId);

    if (!monitorEvent) return;

    selectEvent(monitorEvent);
  });
}

async function refreshEvents() {
  try {
    const events = await fetchMonitorEvents();

    allEvents = events;
    eventsById.clear();

    for (const event of events) {
      eventsById.set(event.id, event);
    }

    lastSuccessfulUpdate = new Date();

    applyFilters();

    setConnectionState('ok');
  } catch (error) {
    console.error(
      '[Black Sea Eco Monitor]',
      error,
    );

    if (allEvents.length && lastSuccessfulUpdate) {
      setConnectionState('warning');
      return;
    }

    setConnectionState(
      'error',
      error.message,
    );
  }
}

map.on('click', (event) => {
  if (!driftSelectionActive) {
    return;
  }

  driftSeed = {
    longitude: event.lngLat.lng,
    latitude: event.lngLat.lat,
  };
  driftSelectionActive = false;
  driftSelectionJustConsumed = true;

  window.setTimeout(
    () => {
      driftSelectionJustConsumed = false;
    },
    0,
  );
  driftPayload = null;
  driftErrorMessage = '';
  map.getCanvas().style.cursor = '';

  renderDriftMap();
  renderDriftControls();
});


map.on('load', () => {
  installRegionalFocus(map);
  installEventLayer();
  installCurrentLayer();
  installDriftLayer();
  renderCurrentsStatus();
  renderCurrentDisplayControls();
  renderDriftControls();

  void refreshEvents();

  window.setInterval(
    refreshEvents,
    REFRESH_INTERVAL_MS,
  );

  window.setInterval(
    () => {
      if (currentLayerVisible()) {
        void refreshCurrents();
      }
    },
    CURRENTS_REFRESH_INTERVAL_MS,
  );
});
