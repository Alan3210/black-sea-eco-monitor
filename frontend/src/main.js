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

const REFRESH_INTERVAL_MS = 60_000;

const statusDot = document.getElementById('connection-dot');
const connectionLabel = document.getElementById('connection-label');
const updateLabel = document.getElementById('update-label');
const eventCount = document.getElementById('event-count');
const resetFiltersButton = document.getElementById('reset-filters');

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

function setConnectionState(state, message, subline) {
  statusDot.className = `status-dot status-dot--${state}`;
  connectionLabel.textContent = message;
  updateLabel.textContent = subline;
}

function formatClock(date) {
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
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
  if (visibleEvents.length === allEvents.length) {
    eventCount.textContent =
      `${visibleEvents.length} ${visibleEvents.length === 1 ? 'event' : 'events'}`;
    return;
  }

  eventCount.textContent =
    `${visibleEvents.length} of ${allEvents.length} events`;
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
    `${group.count} incidents at ${group.locationName}`,
  );

  const count = document.createElement('span');
  count.className = 'colocated-marker__count';
  count.textContent = String(group.count);

  const caption = document.createElement('span');
  caption.className = 'colocated-marker__caption';
  caption.textContent = 'INCIDENTS';

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
        'No evidence records.',
      ),
    );
    return;
  }

  for (const evidence of rows) {
    const item = makeElement('article', 'detail-evidence');

    const title = makeElement(
      'div',
      'detail-evidence__title',
      evidence.title || 'Untitled source',
    );

    const meta = makeElement(
      'div',
      'detail-evidence__meta',
      [
        evidence.source || 'Unknown source',
        formatEventDate(evidence.published_at),
      ].join(' · '),
    );

    item.append(title, meta);

    const safeUrl = safeExternalHttpUrl(evidence.url);

    if (safeUrl) {
      const link = makeElement(
        'a',
        'detail-evidence__link',
        'Open source ↗',
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
    `← ${group.count} incidents at this point`,
  );

  button.type = 'button';

  button.addEventListener('click', () => {
    selectGroup(group);
  });

  return button;
}

function renderEventPanel(event, originGroupId = null) {
  const token = ++panelRenderToken;
  const vm = eventDetailsViewModel(event);

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
    makeMetric('EVENT CONFIDENCE', vm.confidence),
    makeMetric('LOCATION CONFIDENCE', vm.locationConfidence),
    makeMetric('EVIDENCE', String(vm.evidenceCount)),
    makeMetric('COORDINATES', vm.coordinates),
  );

  const locationQuality = makeElement(
    'section',
    'detail-section',
  );

  locationQuality.append(
    makeElement(
      'div',
      'detail-section__title',
      'LOCATION QUALITY',
    ),
  );

  const locationQualityGrid = makeElement(
    'div',
    'detail-quality-grid',
  );

  locationQualityGrid.append(
    makeMetric('LOCATION TYPE', vm.locationType),
    makeMetric('MAP SCOPE', vm.locationScope),
    makeMetric('COORDINATE SOURCE', vm.coordinateSource),
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
      'TIMELINE',
    ),
  );

  const timelineGrid = makeElement(
    'div',
    'detail-timeline',
  );

  timelineGrid.append(
    makeMetric('INCIDENT TIME', vm.incidentTime),
    makeMetric('SOURCE TIME', vm.sourceTime),
    makeMetric('DETECTED', vm.detectionTime),
    makeMetric('FIRST SEEN', vm.firstSeen),
    makeMetric('LATEST', vm.lastSeen),
  );

  timeline.append(timelineGrid);

  const evidenceSection = makeElement(
    'section',
    'detail-section',
  );

  const evidenceHeading = makeElement(
    'div',
    'detail-section__title',
    `EVIDENCE · ${vm.evidenceCount}`,
  );

  const evidenceList = makeElement(
    'div',
    'detail-evidence-list',
  );

  evidenceList.append(
    makeElement(
      'div',
      'evidence-loading',
      'Loading sources…',
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
          `Evidence unavailable: ${error.message}`,
        ),
      );
    });
}

function makeGroupEventCard(event, group) {
  const vm = eventDetailsViewModel(event);

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
    `${vm.severity} severity · ${vm.confidence} confidence · ${vm.evidenceCount} evidence`,
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
    'CO-LOCATED INCIDENTS',
  );

  const location = makeElement(
    'h2',
    'detail-location',
    group.locationName,
  );

  const summary = makeElement(
    'div',
    'detail-headline',
    `${group.count} incidents share this canonical map point. Select one to inspect its evidence and lifecycle.`,
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

    setConnectionState(
      'ok',
      'Monitor online',
      `Updated ${formatClock(lastSuccessfulUpdate)}`,
    );
  } catch (error) {
    console.error(
      '[Black Sea Eco Monitor]',
      error,
    );

    if (allEvents.length && lastSuccessfulUpdate) {
      setConnectionState(
        'warning',
        'Monitor offline',
        `Showing last known data · Updated ${formatClock(lastSuccessfulUpdate)}`,
      );
      return;
    }

    setConnectionState(
      'error',
      'Monitor unavailable',
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
