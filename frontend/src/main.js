import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import './style.css';

import {
  eventsToFeatureCollection,
  fetchEventEvidence,
  fetchMonitorEvents,
} from './events.js';

import {
  DEFAULT_CATEGORIES,
  DEFAULT_STATUSES,
  filterEvents,
} from './filters.js';

const REFRESH_INTERVAL_MS = 60_000;

const statusDot = document.getElementById('connection-dot');
const connectionLabel = document.getElementById('connection-label');
const updateLabel = document.getElementById('update-label');
const eventCount = document.getElementById('event-count');
const resetFiltersButton = document.getElementById('reset-filters');

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

let allEvents = [];
let visibleEvents = [];
let lastSuccessfulUpdate = null;

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

function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleString();
}

function confidenceLabel(value) {
  return Number.isFinite(value)
    ? `${Math.round(value * 100)}%`
    : '—';
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

function applyFilters() {
  visibleEvents = filterEvents(
    allEvents,
    readFilterState(),
  );

  const source = map.getSource('monitor-events');

  if (source) {
    source.setData(
      eventsToFeatureCollection(visibleEvents),
    );
  }

  updateEventCount();
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

function makeTextRow(label, value) {
  const row = document.createElement('div');
  row.className = 'popup-row';

  const key = document.createElement('span');
  key.className = 'popup-key';
  key.textContent = label;

  const val = document.createElement('span');
  val.className = 'popup-value';
  val.textContent = value;

  row.append(key, val);
  return row;
}

function makeEvidenceSection(event) {
  const section = document.createElement('section');
  section.className = 'evidence-section';

  const heading = document.createElement('div');
  heading.className = 'evidence-heading';
  heading.textContent = `EVIDENCE (${event.evidenceCount})`;

  const body = document.createElement('div');
  body.className = 'evidence-list';
  body.textContent = 'Loading sources…';

  section.append(heading, body);

  fetchEventEvidence(event.id)
    .then((rows) => {
      body.replaceChildren();

      if (!rows.length) {
        body.textContent = 'No evidence records.';
        return;
      }

      for (const evidence of rows) {
        const item = document.createElement('article');
        item.className = 'evidence-item';

        const title = document.createElement('div');
        title.className = 'evidence-title';
        title.textContent =
          evidence.title || 'Untitled source';

        const meta = document.createElement('div');
        meta.className = 'evidence-meta';
        meta.textContent = [
          evidence.source || 'Unknown source',
          formatDate(evidence.published_at),
        ].join(' · ');

        item.append(title, meta);

        if (evidence.url) {
          const link = document.createElement('a');
          link.href = evidence.url;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.textContent = 'Open source ↗';
          item.append(link);
        }

        body.append(item);
      }
    })
    .catch((error) => {
      body.textContent =
        `Evidence unavailable: ${error.message}`;
    });

  return section;
}

function buildPopupContent(event) {
  const root = document.createElement('div');
  root.className = 'event-popup';

  const category = document.createElement('div');
  category.className = 'popup-category';
  category.textContent = event.categoryLabel;
  category.style.setProperty(
    '--event-color',
    event.markerColor,
  );

  const title = document.createElement('h2');
  title.textContent = event.locationName;

  const incidentTitle = document.createElement('div');
  incidentTitle.className = 'incident-title';
  incidentTitle.textContent =
    event.primaryTitle || 'Environmental incident';

  root.append(
    category,
    title,
    incidentTitle,
    makeTextRow('Status', event.status),
    makeTextRow('Severity', event.severity),
    makeTextRow(
      'Confidence',
      confidenceLabel(event.confidence),
    ),
    makeTextRow(
      'Coordinates',
      `${event.latitude.toFixed(4)}, ${event.longitude.toFixed(4)}`,
    ),
    makeTextRow(
      'Updated',
      formatDate(event.updatedAt || event.lastSeen),
    ),
    makeEvidenceSection(event),
  );

  return root;
}

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

    new maplibregl.Popup({
      closeButton: true,
      closeOnClick: true,
      maxWidth: '410px',
      offset: 14,
    })
      .setLngLat([
        monitorEvent.longitude,
        monitorEvent.latitude,
      ])
      .setDOMContent(
        buildPopupContent(monitorEvent),
      )
      .addTo(map);
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
