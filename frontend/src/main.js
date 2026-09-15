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

const REFRESH_INTERVAL_MS = 60_000;

const statusDot = document.getElementById('connection-dot');
const connectionLabel = document.getElementById('connection-label');
const updateLabel = document.getElementById('update-label');
const eventCount = document.getElementById('event-count');
const resetFiltersButton = document.getElementById('reset-filters');
const languageButtons = [
  ...document.querySelectorAll('[data-language]'),
];

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

let selectedEventId = null;
let selectedGroupId = null;
let panelRenderToken = 0;

const map = new maplibregl.Map({
  container: 'map',
  center: [35.2, 43.5],
  zoom: 4.7,
  minZoom: 3,
  maxZoom: 14,
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

map.on('load', () => {
  installEventLayer();
  void refreshEvents();

  window.setInterval(
    refreshEvents,
    REFRESH_INTERVAL_MS,
  );
});
