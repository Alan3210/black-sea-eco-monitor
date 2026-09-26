import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import './style.css';
import "./evidencePanel.css";
import {
  isDashboardMode,
  createDashboardRoot,
} from './evidenceDashboardMode.js';

import {
  mountEvidenceDashboard,
} from './evidenceDashboardEntry.js';

import {
  mountFinalEvidencePanel,
} from './finalMapEvidenceMount.js';

import {
  renderVerticalTimeline,
} from './evidenceTimelineUX.js';

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
  CAMS_RUNTIME_CONFIG,
} from './camsAirLiveIntegration.js';

import {
  buildCamsAirCellGeoJSON,
  camsFieldViewModel,
  camsFillColorExpression,
  normalizeCamsOpacityPercent,
} from './camsAirOperationalField.js';
import { installTropomiSatelliteLayer } from './tropomiOperationalField.js';
import { installGeosCfAirLayer } from './geosCfOperationalField.js';

import {
  fetchWindField,
  formatWindSpeed,
  normalizeWindArrowSizePercent,
  windArrowSizeExpression,
  windToFeatureCollection,
} from './wind.js';

import {
  CurrentParticleEngine,
  normalizeCurrentDisplayMode,
  normalizeParticleCount,
  normalizeParticleSpeedPercent,
  normalizeParticleTrailPercent,
} from './currentParticles.js';

import {
  WindParticleEngine,
  normalizeWindDisplayMode,
  normalizeWindParticleCount,
  normalizeWindParticleSpeedPercent,
  normalizeWindParticleTrailPercent,
  normalizeWindParticleSizePercent,
} from './windParticles.js';

import {
  combinedFieldsViewModel,
} from './combinedFields.js';

import {
  DEFAULT_DRIFT_FORCING_MODE,
  DEFAULT_DRIFT_HORIZON,
  DEFAULT_DRIFT_PARTICLES,
  DRIFT_FORCING_CURRENTS_PLUS_WIND,
  driftCenterGeoJSON,
  driftEnvelopeGeoJSON,
  driftForcingViewModel,
  driftPointsGeoJSON,
  driftSeedGeoJSON,
  driftTrackGeoJSON,
  fetchDriftForecast,
  normalizeDriftForcingMode,
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

import {
  fetchSatelliteCandidates,
  satelliteCandidateViewModel,
} from './satellite.js';

import {
  fetchMonitorEventContext,
  monitorContextViewModel,
} from './monitorContext.js';

import {
  renderSourceOverview,
} from './sourceOverviewBlock.js';

import {
  buildShareIncidentSummary,
  renderShareSummary,
} from './shareIncidentSummary.js';

import {
  DEFAULT_IMPACT_THRESHOLD_KM,
  fetchDriftImpact,
  impactAssessmentsToFeatureCollection,
  impactSummaryViewModel,
} from './impact.js';

import {
  eventCanSeedMarineModel,
  satelliteCandidateSeed,
  seedStatusKey,
  modelScenarioShouldPersist,
} from './modelScenario.js';

const REFRESH_INTERVAL_MS = 60_000;
const CURRENTS_REFRESH_INTERVAL_MS = 15 * 60_000;
const CURRENTS_STRIDE = 10;
const WIND_REFRESH_INTERVAL_MS = 15 * 60_000;
const WIND_STRIDE = 2;
const CAMS_AIR_OPACITY_STORAGE_KEY =
  'black-sea-eco-monitor.cams-air-opacity';
const WIND_ARROW_SIZE_STORAGE_KEY =
  'black-sea-eco-monitor.wind-arrow-size';
const WIND_DISPLAY_MODE_STORAGE_KEY =
  'black-sea-eco-monitor.wind-display-mode';
const WIND_PARTICLE_COUNT_STORAGE_KEY =
  'black-sea-eco-monitor.wind-particle-count';
const WIND_PARTICLE_SPEED_STORAGE_KEY =
  'black-sea-eco-monitor.wind-particle-speed';
const WIND_PARTICLE_TRAIL_STORAGE_KEY =
  'black-sea-eco-monitor.wind-particle-trail';
const WIND_PARTICLE_SIZE_STORAGE_KEY =
  'black-sea-eco-monitor.wind-particle-size';
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

// WEATHER1_4_FORCING_MODE_UI
const DRIFT_FORCING_MODE_STORAGE_KEY =
  'black-sea-eco-monitor.drift-forcing-mode';

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

const camsAirToggle = document.getElementById(
  'cams-air-layer-toggle',
);
const camsAirNote = document.getElementById(
  'cams-air-panel',
);
const camsAirPollutantSelect = document.getElementById(
  'cams-air-pollutant',
);
const camsAirOperational = document.getElementById(
  'cams-air-operational',
);
const camsAirValidTime = document.getElementById(
  'cams-air-valid-time',
);
const camsAirMin = document.getElementById(
  'cams-air-min',
);
const camsAirMean = document.getElementById(
  'cams-air-mean',
);
const camsAirMax = document.getElementById(
  'cams-air-max',
);
const camsAirUnits = document.getElementById(
  'cams-air-units',
);
const camsAirLegendMin = document.getElementById(
  'cams-air-legend-min',
);
const camsAirLegendMid = document.getElementById(
  'cams-air-legend-mid',
);
const camsAirLegendMax = document.getElementById(
  'cams-air-legend-max',
);
const camsAirOpacitySlider = document.getElementById(
  'cams-air-opacity',
);
const camsAirOpacityValue = document.getElementById(
  'cams-air-opacity-value',
);

const windToggle = document.getElementById(
  'wind-layer-toggle',
);
const windNote = document.getElementById(
  'wind-layer-note',
);
const windArrowSizeSlider = document.getElementById(
  'wind-arrow-size',
);
const windArrowSizeValue = document.getElementById(
  'wind-arrow-size-value',
);

const windDisplayModeInputs = [
  ...document.querySelectorAll(
    'input[name="wind-display-mode"]',
  ),
];

const windParticleControls = document.getElementById(
  'wind-particle-controls',
);

const windParticleCountSlider = document.getElementById(
  'wind-particle-count',
);

const windParticleCountValue = document.getElementById(
  'wind-particle-count-value',
);

const windParticleSpeedSlider = document.getElementById(
  'wind-particle-speed',
);

const windParticleSpeedValue = document.getElementById(
  'wind-particle-speed-value',
);

const windParticleTrailSlider = document.getElementById(
  'wind-particle-trail',
);

const windParticleTrailValue = document.getElementById(
  'wind-particle-trail-value',
);

const windParticleSizeSlider = document.getElementById(
  'wind-particle-size',
);

const windParticleSizeValue = document.getElementById(
  'wind-particle-size-value',
);

const combinedFieldsHud = document.getElementById(
  'combined-fields-hud',
);

const combinedFieldsState = document.getElementById(
  'combined-fields-state',
);

const combinedCurrentMode = document.getElementById(
  'combined-current-mode',
);

const combinedCurrentTime = document.getElementById(
  'combined-current-time',
);

const combinedWindMode = document.getElementById(
  'combined-wind-mode',
);

const combinedWindTime = document.getElementById(
  'combined-wind-time',
);

const combinedWindSpeed = document.getElementById(
  'combined-wind-speed',
);

const combinedFieldsTimeDelta = document.getElementById(
  'combined-fields-time-delta',
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
const driftForcingInputs = [
  ...document.querySelectorAll(
    'input[name="drift-forcing-mode"]',
  ),
];
const driftForcingDetails = document.getElementById(
  'drift-forcing-details',
);
const driftScopeNote = document.getElementById(
  'drift-scope-note',
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

const satelliteToggle = document.getElementById(
  'satellite-layer-toggle',
);
const satelliteNote = document.getElementById(
  'satellite-layer-note',
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
const contextCache = new Map();
const contextRequests = new Map();


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

let camsAirPayload = null;
let camsAirLoading = false;
let camsAirErrorMessage = '';
let camsAirPollutant = 'pm25';
let camsAirPopup = null;
let camsAirOpacityPercent =
  normalizeCamsOpacityPercent(
    window.localStorage.getItem(
      CAMS_AIR_OPACITY_STORAGE_KEY,
    ),
    55,
  );

let windPayload = null;
let windLoading = false;
let windErrorMessage = '';
let windPopup = null;

let windArrowSizePercent =
  normalizeWindArrowSizePercent(
    window.localStorage.getItem(
      WIND_ARROW_SIZE_STORAGE_KEY,
    ),
    100,
  );

let windDisplayMode =
  normalizeWindDisplayMode(
    window.localStorage.getItem(
      WIND_DISPLAY_MODE_STORAGE_KEY,
    ),
    'arrows',
  );

let windParticleCount =
  normalizeWindParticleCount(
    window.localStorage.getItem(
      WIND_PARTICLE_COUNT_STORAGE_KEY,
    ),
    (
      navigator.hardwareConcurrency
      && navigator.hardwareConcurrency <= 4
    )
      ? 700
      : (
        navigator.hardwareConcurrency
        && navigator.hardwareConcurrency <= 8
      )
        ? 1000
        : 1400,
  );

let windParticleSpeedPercent =
  normalizeWindParticleSpeedPercent(
    window.localStorage.getItem(
      WIND_PARTICLE_SPEED_STORAGE_KEY,
    ),
    100,
  );

let windParticleTrailPercent =
  normalizeWindParticleTrailPercent(
    window.localStorage.getItem(
      WIND_PARTICLE_TRAIL_STORAGE_KEY,
    ),
    55,
  );

let windParticleSizePercent =
  normalizeWindParticleSizePercent(
    window.localStorage.getItem(
      WIND_PARTICLE_SIZE_STORAGE_KEY,
    ),
    120,
  );

let windParticleEngine = null;

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
let driftSeedSourceEventId = null;
let driftForecastSourceEventId = null;
let driftSeedSourceKind = null;
let driftSeedSourceId = null;
let driftForecastSourceKind = null;
let driftForecastSourceId = null;

let impactPayload = null;
let impactLoading = false;
let impactErrorMessage = '';
let impactEventId = null;
let impactRequestToken = 0;

let satelliteCandidatesPayload = null;



let satelliteCandidatesLoading = false;
let satelliteCandidatesErrorMessage = '';
let satellitePopup = null;

let currentsLoadingStartedAt = null;
let driftLoadingStartedAt = null;
let longTaskTicker = null;

let driftForcingMode = normalizeDriftForcingMode(
  window.localStorage.getItem(
    DRIFT_FORCING_MODE_STORAGE_KEY,
  ),
  DEFAULT_DRIFT_FORCING_MODE,
);

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


if (isDashboardMode()) {
  const root = createDashboardRoot();

  void mountEvidenceDashboard(root);

  // Dashboard mode skips MapLibre bootstrap.
  throw new Error('Dashboard mode active');
}

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

// SYSTEM4_2_PERSISTENT_MODEL_SCENARIO
function modelScenarioActive() {
  return modelScenarioShouldPersist({
    seedAvailable: Boolean(driftSeed),
    forecastAvailable: Boolean(driftPayload),
    driftLoading,
    impactAvailable: Boolean(impactPayload),
    impactLoading,
    impactError: Boolean(impactErrorMessage),
  });
}

function renderStandaloneModelScenarioPanel() {
  panelRenderToken += 1;
  eventPanelContent.replaceChildren();

  const workflowSection = makeElement(
    'section',
    'detail-section model-workflow',
  );

  workflowSection.append(
    makeElement(
      'div',
      'detail-section__title',
      t(currentLanguage, 'workflow.title'),
    ),
  );

  const workflowContent = makeElement(
    'div',
    'workflow-content',
  );

  renderModelWorkflow(workflowContent, null);
  workflowSection.append(workflowContent);
  eventPanelContent.append(workflowSection);

  eventPanel.classList.add('event-panel--open');
  eventPanel.setAttribute('aria-hidden', 'false');
}

function closeEventPanelIfIdle() {
  if (
    selectedEventId
    || selectedGroupId
    || modelScenarioActive()
  ) {
    return;
  }

  eventPanel.classList.remove('event-panel--open');
  eventPanel.setAttribute('aria-hidden', 'true');
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
      return;
    }
  }

  if (modelScenarioActive()) {
    renderStandaloneModelScenarioPanel();
    return;
  }

  closeEventPanelIfIdle();
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

function loadContext(eventId) {
  if (contextCache.has(eventId)) {
    return Promise.resolve(
      contextCache.get(eventId),
    );
  }

  if (contextRequests.has(eventId)) {
    return contextRequests.get(eventId);
  }

  const request = fetchMonitorEventContext(eventId)
    .then((context) => {
      contextCache.set(eventId, context);
      return context;
    })
    .finally(() => {
      contextRequests.delete(eventId);
    });

  contextRequests.set(eventId, request);
  return request;
}

function renderContextGrid(container, context) {
  container.replaceChildren();

  const vm = monitorContextViewModel(context);
  const yesNo = (value) => t(
    currentLanguage,
    value ? 'panel.ready' : 'panel.unavailable',
  );

  container.append(
    makeMetric(
      t(currentLanguage, 'panel.satelliteObservations'),
      String(vm.satelliteCount),
    ),
    makeMetric(
      t(currentLanguage, 'panel.driftReady'),
      yesNo(vm.driftReady),
    ),
    makeMetric(
      t(currentLanguage, 'panel.impactReady'),
      yesNo(vm.impactReady),
    ),
    makeMetric(
      t(currentLanguage, 'panel.arReady'),
      yesNo(vm.arReady),
    ),
  );
}

function makeWorkflowButton(
  label,
  className = 'workflow-button',
) {
  const button = makeElement(
    'button',
    className,
    label,
  );
  button.type = 'button';
  return button;
}


function formatImpactDistance(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return null;
  }

  return number < 10
    ? `${number.toFixed(2)} km`
    : `${number.toFixed(1)} km`;
}


function renderModelWorkflow(container, event) {
  container.replaceChildren();

  const eventHasCoordinates = Boolean(
    Number.isFinite(Number(event?.latitude))
    && Number.isFinite(Number(event?.longitude)),
  );

  const eventSeedEligible = eventCanSeedMarineModel(
    event,
  );

  const seedAvailable = Boolean(driftSeed);
  const forecastAvailable = Boolean(driftPayload);

  const impactMatchesScenario = Boolean(
    impactPayload,
  );

  const status = makeElement(
    'div',
    'workflow-status',
  );

  if (driftLoading && seedAvailable) {
    status.textContent = t(
      currentLanguage,
      'workflow.modelBusy',
    );
  } else if (forecastAvailable) {
    status.textContent = t(
      currentLanguage,
      seedStatusKey(
        driftForecastSourceKind,
        { forecastReady: true },
      ),
    );
  } else if (seedAvailable) {
    status.textContent = t(
      currentLanguage,
      seedStatusKey(driftSeedSourceKind),
    );
  } else {
    status.textContent = t(
      currentLanguage,
      'workflow.awaiting',
    );
  }

  const actions = makeElement(
    'div',
    'workflow-actions',
  );

  const prepareButton = makeWorkflowButton(
    t(currentLanguage, 'workflow.prepare'),
  );

  prepareButton.disabled = (
    !eventHasCoordinates
    || !eventSeedEligible
    || driftLoading
  );

  prepareButton.addEventListener(
    'click',
    () => {
      prepareDriftFromEvent(event);
    },
  );

  const screenButton = makeWorkflowButton(
    t(
      currentLanguage,
      impactLoading
        ? 'workflow.screeningButton'
        : 'workflow.screen',
      {
        km: DEFAULT_IMPACT_THRESHOLD_KM,
      },
    ),
    'workflow-button workflow-button--secondary',
  );

  screenButton.disabled = (
    !forecastAvailable
    || driftLoading
    || impactLoading
  );

  screenButton.addEventListener(
    'click',
    () => {
      void runImpactScreening(event);
    },
  );

  if (event) {
    actions.append(prepareButton);
  }

  actions.append(screenButton);

  container.append(
    status,
    actions,
  );

  if (event && !eventSeedEligible) {
    container.append(
      makeElement(
        'div',
        'workflow-disclaimer',
        t(
          currentLanguage,
          'workflow.eventPointUnavailable',
        ),
      ),
    );
  }

  if (impactLoading) {
    container.append(
      makeElement(
        'div',
        'workflow-loading',
        t(currentLanguage, 'workflow.screening'),
      ),
    );
  } else if (impactErrorMessage) {
    container.append(
      makeElement(
        'div',
        'workflow-error',
        t(
          currentLanguage,
          'workflow.screenError',
          { message: impactErrorMessage },
        ),
      ),
    );
  } else if (impactMatchesScenario) {
    const vm = impactSummaryViewModel(
      impactPayload,
    );

    const heading = makeElement(
      'div',
      'workflow-result-title',
      t(currentLanguage, 'workflow.summary'),
    );

    const summaryGrid = makeElement(
      'div',
      'workflow-summary-grid',
    );

    summaryGrid.append(
      makeMetric(
        t(currentLanguage, 'workflow.targets'),
        String(vm.targetCount),
      ),
      makeMetric(
        t(currentLanguage, 'workflow.withinThreshold'),
        String(vm.withinThresholdCount),
      ),
      makeMetric(
        t(currentLanguage, 'workflow.threshold'),
        `${vm.thresholdKm} km`,
      ),
    );

    const list = makeElement(
      'div',
      'workflow-assessment-list',
    );

    for (const assessment of vm.assessments) {
      const target = assessment?.target ?? {};
      const card = makeElement(
        'article',
        'workflow-assessment',
      );

      const top = makeElement(
        'div',
        'workflow-assessment__top',
      );

      top.append(
        makeElement(
          'div',
          'workflow-assessment__name',
          String(
            target.name
            ?? t(
              currentLanguage,
              'workflow.unknownTarget',
            ),
          ),
        ),
      );

      top.append(
        makeElement(
          'span',
          assessment?.potentially_affected
            ? 'workflow-assessment__badge workflow-assessment__badge--within'
            : 'workflow-assessment__badge',
          t(
            currentLanguage,
            assessment?.potentially_affected
              ? 'workflow.within'
              : 'workflow.outside',
          ),
        ),
      );

      const meta = [];

      if (
        assessment?.first_exposure_hours
        !== null
        && assessment?.first_exposure_hours
        !== undefined
      ) {
        meta.push(
          t(
            currentLanguage,
            'workflow.firstExposure',
            {
              hours:
                assessment.first_exposure_hours,
            },
          ),
        );
      }

      const distance = formatImpactDistance(
        assessment?.minimum_distance_km,
      );

      meta.push(
        distance
          ? t(
            currentLanguage,
            'workflow.closest',
            { distance },
          )
          : t(
            currentLanguage,
            'workflow.noDistance',
          ),
      );

      card.append(
        top,
        makeElement(
          'div',
          'workflow-assessment__meta',
          meta.join(' · '),
        ),
      );

      list.append(card);
    }

    container.append(
      heading,
      summaryGrid,
      list,
    );
  }

  container.append(
    makeElement(
      'div',
      'workflow-disclaimer',
      t(currentLanguage, 'workflow.disclaimer'),
    ),
  );
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

    const evidenceTimelineSection = makeElement(
    'section',
    'detail-section evidence-timeline-section',
  );

  evidenceTimelineSection.append(
    makeElement(
      'div',
      'detail-section__title',
      'Evidence Timeline',
    ),
  );

  const evidenceTimelineContainer = makeElement(
    'div',
    'evidence-vertical-timeline',
  );

  evidenceTimelineContainer.innerHTML =
    renderVerticalTimeline([
      {
        type: 'observation',
        title: 'Satellite observation',
        source: 'Sentinel-5P',
        time: '13.09 01:30',
      },
      {
        type: 'model',
        title: 'CAMS forecast',
        source: 'CAMS',
        time: '13.09 02:00',
      },
      {
        type: 'detection',
        title: 'Event detected',
        source: 'Monitor',
        time: '13.09 08:00',
      },
      {
        type: 'confirmation',
        title: 'Evidence update',
        source: 'Evidence System',
        time: '13.09 10:54',
      },
    ]);

  evidenceTimelineSection.append(
    evidenceTimelineContainer,
  );

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

  const contextSection = makeElement(
    'section',
    'detail-section',
  );

  contextSection.append(
    makeElement(
      'div',
      'detail-section__title',
      t(currentLanguage, 'panel.systemContext'),
    ),
  );

  const contextGrid = makeElement(
    'div',
    'detail-context-grid',
  );

  contextGrid.append(
    makeElement(
      'div',
      'evidence-loading detail-context-status',
      t(currentLanguage, 'panel.contextLoading'),
    ),
  );

  contextSection.append(contextGrid);

  const workflowSection = makeElement(
    'section',
    'detail-section model-workflow',
  );

  workflowSection.append(
    makeElement(
      'div',
      'detail-section__title',
      t(currentLanguage, 'workflow.title'),
    ),
  );

  const workflowContent = makeElement(
    'div',
    'workflow-content',
  );

  renderModelWorkflow(
    workflowContent,
    event,
  );

  workflowSection.append(
    workflowContent,
  );

  const sourceOverviewSection = makeElement(
    'section',
    'detail-section source-overview-section',
  );

  sourceOverviewSection.innerHTML = `
    <div class="detail-section__title">
      ${t(currentLanguage, 'sources.title')}
    </div>
    ${renderSourceOverview([
      {
        name: 'Sentinel-5P',
        type: 'Satellite',
        purpose: 'Observation',
      },
      {
        name: 'CAMS',
        type: 'Model',
        purpose: 'Forecast',
      },
      {
        name: 'Drift Model',
        type: 'Simulation',
        purpose: 'Prediction',
      },
    ])}
  `;

  const shareSummarySection = makeElement(
    'section',
    'detail-section share-summary-section',
  );

  shareSummarySection.innerHTML =
    renderShareSummary(
      buildShareIncidentSummary({
        title: vm.location || event.title || "Incident",
        location: null,
        evidence: vm.evidenceCount
          ? Array.from({ length: vm.evidenceCount })
          : [],
        timeline: [
          {
            title: "Satellite observation",
          },
          {
            title: "CAMS forecast",
          },
          {
            title: "Event detected",
          },
          {
            title: "Evidence update",
          },
        ],
        impact: impactPayload || {
          status: "not_calculated",
        },
      }),
    );

  const impactForecastSection = makeElement(
    'section',
    'detail-section impact-summary-section',
  );

  const impactVm = impactPayload
    ? impactSummaryViewModel(impactPayload)
    : null;

  impactForecastSection.innerHTML = `
    <div
      class="detail-section__title"
      data-i18n="impact.title"
    >
      ${t(currentLanguage, 'impact.title')}
    </div>

    <div class="detail-metrics">
      <div class="detail-metric">
        <div
          class="detail-metric__label"
          data-i18n="impact.targets"
        >
          ${t(currentLanguage, 'impact.targets')}
        </div>

        <div class="detail-metric__value">
          ${impactVm ? impactVm.targetCount : "—"}
        </div>
      </div>
    </div>
  `;

  eventPanelContent.append(
    header,
    pills,
    metrics,
    locationQuality,
    timeline,
    evidenceTimelineSection,
    impactForecastSection,
    sourceOverviewSection,
    evidenceSection,
    shareSummarySection,
    contextSection,
    workflowSection,
  );

 
  eventPanel.classList.add(
    'event-panel--open',
  );

  eventPanel.setAttribute(
    'aria-hidden',
    'false',
  );

  loadContext(event.id)
    .then((context) => {
      if (
        token !== panelRenderToken
        || selectedEventId !== event.id
      ) {
        return;
      }

      renderContextGrid(
        contextGrid,
        context,
      );
    })
    .catch((error) => {
      if (
        token !== panelRenderToken
        || selectedEventId !== event.id
      ) {
        return;
      }

      contextGrid.replaceChildren(
        makeElement(
          'div',
          'evidence-error detail-context-status',
          t(
            currentLanguage,
            'panel.contextUnavailable',
            { message: error.message },
          ),
        ),
      );
    });

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

  if (modelScenarioActive()) {
    renderStandaloneModelScenarioPanel();
    return;
  }

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
  for (const input of driftForcingInputs) {
    input.checked = input.value === driftForcingMode;
    input.disabled = driftLoading;
  }

  for (const input of driftHorizonInputs) {
    input.checked = Number(input.value) === driftHorizon;
  }

  if (driftParticlesSlider) {
    driftParticlesSlider.value = String(driftParticles);
  }

  if (driftParticlesValue) {
    driftParticlesValue.textContent = String(driftParticles);
  }

  const forcingView = driftForcingViewModel(
    driftPayload,
    driftForcingMode,
  );
  const windagePercent = Math.round(
    forcingView.windDriftFactor * 100,
  );

  if (driftForcingDetails) {
    if (!forcingView.windEnabled) {
      driftForcingDetails.textContent = t(
        currentLanguage,
        'drift.forcingCurrentSummary',
      );
    } else if (
      forcingView.forecastReferenceTime
    ) {
      const source = forcingView.sources.length
        ? forcingView.sources.join(', ')
        : 'ECMWF';

      driftForcingDetails.textContent = t(
        currentLanguage,
        'drift.forcingWindReady',
        {
          run: formatCurrentValidTime(
            forcingView.forecastReferenceTime,
            localeForLanguage(currentLanguage),
          ),
          source,
          windage: windagePercent,
        },
      );
    } else {
      driftForcingDetails.textContent = t(
        currentLanguage,
        'drift.forcingWindPlanned',
        {
          windage: windagePercent,
        },
      );
    }
  }

  if (driftScopeNote) {
    driftScopeNote.textContent = t(
      currentLanguage,
      forcingView.windEnabled
        ? 'drift.scopeCurrentsWind'
        : 'drift.scopeCurrentOnly',
      {
        windage: windagePercent,
      },
    );
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


function clearImpactMapData() {
  setGeoJSONSourceData(
    'impact-targets',
    emptyFeatureCollection(),
  );
}


function clearImpactScreening() {
  impactRequestToken += 1;
  impactPayload = null;
  impactLoading = false;
  impactErrorMessage = '';
  impactEventId = null;
  clearImpactMapData();
}


function renderImpactMap() {
  setGeoJSONSourceData(
    'impact-targets',
    impactAssessmentsToFeatureCollection(
      impactPayload,
    ),
  );
}


function prepareDriftFromEvent(event) {
  if (!eventCanSeedMarineModel(event)) {
    return;
  }

  const longitude = Number(event?.longitude);
  const latitude = Number(event?.latitude);

  if (
    !Number.isFinite(longitude)
    || !Number.isFinite(latitude)
  ) {
    return;
  }

  driftSelectionActive = false;
  driftSelectionJustConsumed = false;
  driftSeed = {
    longitude,
    latitude,
  };
  driftSeedSourceEventId = event.id;
  driftForecastSourceEventId = null;
  driftSeedSourceKind = 'event';
  driftSeedSourceId = event.id;
  driftForecastSourceKind = null;
  driftForecastSourceId = null;
  driftPayload = null;
  driftErrorMessage = '';

  clearImpactScreening();

  map.getCanvas().style.cursor = '';
  renderDriftMap();
  renderDriftControls();
  refreshSelectedPanel();
}


async function runImpactScreening(event = null) {
  if (
    impactLoading
    || !driftPayload
  ) {
    return;
  }

  const requestToken = ++impactRequestToken;

  impactLoading = true;
  impactErrorMessage = '';
  impactEventId = event?.id ?? null;

  clearImpactMapData();
  refreshSelectedPanel();

  try {
    const payload = await fetchDriftImpact(
      driftPayload,
      {
        thresholdKm:
          DEFAULT_IMPACT_THRESHOLD_KM,
      },
    );

    if (requestToken !== impactRequestToken) {
      return;
    }

    impactPayload = payload;
    renderImpactMap();
  } catch (error) {
    if (requestToken !== impactRequestToken) {
      return;
    }

    console.error(
      '[Black Sea Eco Monitor / impact]',
      error,
    );

    impactPayload = null;
    impactErrorMessage =
      error?.message || String(error);

    clearImpactMapData();
  } finally {
    if (requestToken === impactRequestToken) {
      impactLoading = false;
      refreshSelectedPanel();
    }
  }
}


function installImpactLayer() {
  map.addSource(
    'impact-targets',
    {
      type: 'geojson',
      data: emptyFeatureCollection(),
    },
  );

  map.addLayer({
    id: 'impact-targets-halo',
    type: 'circle',
    source: 'impact-targets',
    paint: {
      'circle-radius': [
        'case',
        ['==', ['get', 'withinThreshold'], true],
        16,
        11,
      ],
      'circle-color': [
        'case',
        ['==', ['get', 'withinThreshold'], true],
        '#ffd166',
        '#78dce8',
      ],
      'circle-opacity': [
        'case',
        ['==', ['get', 'withinThreshold'], true],
        0.24,
        0.11,
      ],
      'circle-blur': 0.45,
    },
  });

  map.addLayer({
    id: 'impact-targets',
    type: 'circle',
    source: 'impact-targets',
    paint: {
      'circle-radius': [
        'case',
        ['==', ['get', 'withinThreshold'], true],
        7,
        5,
      ],
      'circle-color': [
        'case',
        ['==', ['get', 'withinThreshold'], true],
        '#ffd166',
        '#78dce8',
      ],
      'circle-stroke-color': '#0a1720',
      'circle-stroke-width': 2,
      'circle-opacity': 0.94,
    },
  });
}


function clearDriftForecast() {
  driftSelectionActive = false;
  driftSeed = null;
  driftPayload = null;
  driftLoading = false;
  driftErrorMessage = '';
  driftSeedSourceEventId = null;
  driftForecastSourceEventId = null;
  driftSeedSourceKind = null;
  driftSeedSourceId = null;
  driftForecastSourceKind = null;
  driftForecastSourceId = null;
  clearImpactScreening();
  stopLongTask('drift');
  map.getCanvas().style.cursor = '';
  clearDriftMapData();
  renderDriftControls();
  refreshSelectedPanel();
}


async function runDriftForecast() {
  if (!driftSeed || driftLoading) {
    return;
  }

  driftLoading = true;
  driftErrorMessage = '';
  driftForecastSourceEventId = null;
  driftForecastSourceKind = null;
  driftForecastSourceId = null;
  clearImpactScreening();
  startLongTask('drift');
  renderDriftControls();
  refreshSelectedPanel();

  try {
    const payload = await fetchDriftForecast({
      longitude: driftSeed.longitude,
      latitude: driftSeed.latitude,
      hours: driftHorizon,
      particles: driftParticles,
      forcingMode: driftForcingMode,
    });

    driftPayload = payload;
    driftForecastSourceEventId =
      driftSeedSourceEventId;
    driftForecastSourceKind =
      driftSeedSourceKind;
    driftForecastSourceId =
      driftSeedSourceId;
    renderDriftMap();
  } catch (error) {
    console.error('[Black Sea Eco Monitor drift]', error);
    driftPayload = null;
    driftForecastSourceEventId = null;
    driftForecastSourceKind = null;
    driftForecastSourceId = null;
    driftErrorMessage = error?.message || String(error);
    clearDriftMapData({ keepSeed: true });
  } finally {
    driftLoading = false;
    stopLongTask('drift');
    renderDriftControls();
    refreshSelectedPanel();
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



function combinedModeLabel(
  kind,
  mode,
) {
  const keys =
    kind === 'wind'
      ? {
        arrows:
          'weather.modeArrows',
        particles:
          'weather.modeParticles',
        both:
          'weather.modeBoth',
      }
      : {
        arrows:
          'ocean.modeArrows',
        particles:
          'ocean.modeParticles',
        both:
          'ocean.modeBoth',
      };

  return t(
    currentLanguage,
    keys[mode]
      ?? keys.arrows,
  );
}



function combinedWindSpeedLabel(
  speedMs,
) {
  const speed =
    Number(speedMs);

  if (
    !Number.isFinite(speed)
    || speed < 0
  ) {
    return t(
      currentLanguage,
      'combined.windMeanSpeedUnavailable',
    );
  }

  const formatted =
    new Intl.NumberFormat(
      localeForLanguage(
        currentLanguage,
      ),
      {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      },
    )
      .format(
        speed,
      );

  return t(
    currentLanguage,
    'combined.windMeanSpeed',
    {
      speed:
        formatted,
    },
  );
}


function combinedTimeDeltaLabel(
  minutes,
) {
  if (!Number.isFinite(minutes)) {
    return t(
      currentLanguage,
      'combined.deltaUnknown',
    );
  }

  const rounded =
    Math.max(
      0,
      Math.round(minutes),
    );

  if (rounded < 60) {
    return t(
      currentLanguage,
      'combined.deltaMinutes',
      {
        minutes: rounded,
      },
    );
  }

  const hours =
    Math.floor(
      rounded / 60,
    );

  const remainder =
    rounded % 60;

  if (!remainder) {
    return t(
      currentLanguage,
      'combined.deltaHours',
      {
        hours,
      },
    );
  }

  return t(
    currentLanguage,
    'combined.deltaHoursMinutes',
    {
      hours,
      minutes:
        remainder,
    },
  );
}


function renderCombinedFieldsHud() {
  if (!combinedFieldsHud) {
    return;
  }

  const view =
    combinedFieldsViewModel({
      currentsEnabled:
        currentLayerVisible(),
      windEnabled:
        windLayerVisible(),
      currentsPayload,
      windPayload,
      currentsLoading,
      windLoading,
      currentsError:
        currentsErrorMessage,
      windError:
        windErrorMessage,
      currentDisplayMode,
      windDisplayMode,
    });

  combinedFieldsHud.hidden =
    !view.visible;

  if (!view.visible) {
    return;
  }

  combinedFieldsHud.dataset.state =
    view.state;

  if (combinedFieldsState) {
    const stateKey =
      view.state === 'error'
        ? 'combined.error'
        : (
          view.state === 'loading'
            ? 'combined.loading'
            : 'combined.ready'
        );

    combinedFieldsState.textContent =
      t(
        currentLanguage,
        stateKey,
      );
  }

  if (combinedCurrentMode) {
    combinedCurrentMode.textContent =
      combinedModeLabel(
        'current',
        view.currentDisplayMode,
      );
  }

  if (combinedWindMode) {
    combinedWindMode.textContent =
      combinedModeLabel(
        'wind',
        view.windDisplayMode,
      );
  }

  if (combinedCurrentTime) {
    combinedCurrentTime.textContent =
      view.currentValidTime
        ? formatCurrentValidTime(
          view.currentValidTime,
          localeForLanguage(
            currentLanguage,
          ),
        )
        : '—';
  }

  if (combinedWindTime) {
    combinedWindTime.textContent =
      view.windValidTime
        ? formatCurrentValidTime(
          view.windValidTime,
          localeForLanguage(
            currentLanguage,
          ),
        )
        : '—';
  }

  if (combinedWindSpeed) {
    combinedWindSpeed.textContent =
      combinedWindSpeedLabel(
        view.windMeanSpeedMs,
      );
  }

  if (combinedFieldsTimeDelta) {
    combinedFieldsTimeDelta.textContent =
      combinedTimeDeltaLabel(
        view.timeDeltaMinutes,
      );
  }
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
  renderCombinedFieldsHud();

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


for (const input of driftForcingInputs) {
  input.addEventListener('change', () => {
    if (!input.checked) return;

    const nextMode = normalizeDriftForcingMode(
      input.value,
    );

    if (nextMode === driftForcingMode) {
      renderDriftControls();
      return;
    }

    driftForcingMode = nextMode;

    window.localStorage.setItem(
      DRIFT_FORCING_MODE_STORAGE_KEY,
      driftForcingMode,
    );

    // A forecast calculated with different physical forcing must
    // never remain active after the user switches forcing mode.
    if (driftPayload) {
      driftPayload = null;
      driftForecastSourceEventId = null;
      clearImpactScreening();
      clearDriftMapData({ keepSeed: true });
    }

    renderDriftControls();
    refreshSelectedPanel();
  });
}


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
      driftForecastSourceEventId = null;
      driftForecastSourceKind = null;
      driftForecastSourceId = null;
      clearImpactScreening();
      clearDriftMapData({ keepSeed: true });
    }

    renderDriftControls();
    refreshSelectedPanel();
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
  renderCombinedFieldsHud();

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


// WEATHER-1.5C · animated ECMWF IFS 10 m wind particles.
function windModeShowsArrows() {
  return [
    'arrows',
    'both',
  ].includes(
    windDisplayMode,
  );
}


function windModeShowsParticles() {
  return [
    'particles',
    'both',
  ].includes(
    windDisplayMode,
  );
}


function renderWindDisplayControls() {
  for (
    const input
    of windDisplayModeInputs
  ) {
    input.checked =
      input.value
      === windDisplayMode;
  }

  if (windParticleCountSlider) {
    windParticleCountSlider.value =
      String(
        windParticleCount,
      );
  }

  if (windParticleCountValue) {
    windParticleCountValue.textContent =
      String(
        windParticleCount,
      );
  }

  if (windParticleSpeedSlider) {
    windParticleSpeedSlider.value =
      String(
        windParticleSpeedPercent,
      );
  }

  if (windParticleSpeedValue) {
    windParticleSpeedValue.textContent =
      `${windParticleSpeedPercent}%`;
  }

  if (windParticleTrailSlider) {
    windParticleTrailSlider.value =
      String(
        windParticleTrailPercent,
      );
  }

  if (windParticleTrailValue) {
    windParticleTrailValue.textContent =
      `${windParticleTrailPercent}%`;
  }

  if (windParticleSizeSlider) {
    windParticleSizeSlider.value =
      String(
        windParticleSizePercent,
      );
  }

  if (windParticleSizeValue) {
    windParticleSizeValue.textContent =
      `${windParticleSizePercent}%`;
  }

  const particlesEnabled =
    windModeShowsParticles();

  windParticleControls
    ?.classList.toggle(
      'particle-controls--disabled',
      !particlesEnabled,
    );

  for (
    const input
    of [
      windParticleCountSlider,
      windParticleSpeedSlider,
      windParticleTrailSlider,
      windParticleSizeSlider,
    ]
  ) {
    if (input) {
      input.disabled =
        !particlesEnabled;
    }
  }

  const arrowControl =
    windArrowSizeSlider
      ?.closest(
        '.current-size-control',
      );

  arrowControl?.classList.toggle(
    'current-size-control--disabled',
    !windModeShowsArrows(),
  );

  if (windArrowSizeSlider) {
    windArrowSizeSlider.disabled =
      !windModeShowsArrows();
  }
}


function ensureWindParticleEngine() {
  if (windParticleEngine) {
    return windParticleEngine;
  }

  const mapCanvasContainer =
    map.getCanvasContainer();

  const canvas =
    document.createElement(
      'canvas',
    );

  canvas.id =
    'wind-particles-canvas';

  canvas.className =
    'wind-particles-canvas';

  canvas.setAttribute(
    'aria-hidden',
    'true',
  );

  mapCanvasContainer.append(
    canvas,
  );

  windParticleEngine =
    new WindParticleEngine({
      canvas,
      map,
      particleCount:
        windParticleCount,
      speedPercent:
        windParticleSpeedPercent,
      trailPercent:
        windParticleTrailPercent,
      sizePercent:
        windParticleSizePercent,
    });

  if (windPayload) {
    windParticleEngine.setField(
      windPayload,
    );
  }

  return windParticleEngine;
}


function syncWindVisualization() {
  renderWindDisplayControls();
  renderCombinedFieldsHud();

  const layerEnabled =
    windLayerVisible();

  const arrowVisibility =
    (
      layerEnabled
      && windModeShowsArrows()
    )
      ? 'visible'
      : 'none';

  if (
    map.getLayer(
      'weather-wind-arrows',
    )
  ) {
    map.setLayoutProperty(
      'weather-wind-arrows',
      'visibility',
      arrowVisibility,
    );
  }

  if (
    !layerEnabled
    || !windModeShowsParticles()
    || !windPayload
    || document.hidden
    || mapIsMoving
  ) {
    windParticleEngine?.stop();
  } else {
    const engine =
      ensureWindParticleEngine();

    engine.setParticleCount(
      windParticleCount,
    );

    engine.setSpeedPercent(
      windParticleSpeedPercent,
    );

    engine.setTrailPercent(
      windParticleTrailPercent,
    );

    engine.setSizePercent(
      windParticleSizePercent,
    );

    engine.start();
  }

  if (
    !layerEnabled
    && windPopup
  ) {
    windPopup.remove();
    windPopup = null;
  }
}


// WEATHER-1.5B · ECMWF IFS 10 m wind visualization.
function createWindArrowImage() {
  const size = 96;
  const canvas =
    document.createElement(
      'canvas',
    );

  canvas.width = size;
  canvas.height = size;

  const context =
    canvas.getContext('2d');

  context.clearRect(
    0,
    0,
    size,
    size,
  );

  // Arrow artwork points to true north before MapLibre rotation.
  context.beginPath();
  context.moveTo(48, 7);
  context.lineTo(79, 37);
  context.lineTo(61, 37);
  context.lineTo(61, 88);
  context.lineTo(35, 88);
  context.lineTo(35, 37);
  context.lineTo(17, 37);
  context.closePath();

  context.save();
  context.shadowColor =
    'rgba(56, 189, 248, 0.72)';
  context.shadowBlur = 10;
  context.fillStyle = '#38bdf8';
  context.fill();
  context.restore();

  context.strokeStyle =
    'rgba(8, 20, 27, 0.98)';
  context.lineWidth = 9;
  context.lineJoin = 'round';
  context.stroke();

  context.fillStyle = '#38bdf8';
  context.fill();

  context.strokeStyle = '#d9f7ff';
  context.lineWidth = 2.5;
  context.stroke();

  return context.getImageData(
    0,
    0,
    size,
    size,
  );
}



// AIR-1.3C.9 · operational CAMS field.
function formatCamsConcentration(value) {
  const numeric = Number(value);

  if (!Number.isFinite(numeric)) return '—';

  return new Intl.NumberFormat(
    localeForLanguage(currentLanguage),
    {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    },
  ).format(numeric);
}


function camsAirLayerVisible() {
  return Boolean(camsAirToggle?.checked);
}


function applyCamsAirOpacity() {
  if (camsAirOpacitySlider) {
    camsAirOpacitySlider.value =
      String(camsAirOpacityPercent);
  }

  if (camsAirOpacityValue) {
    camsAirOpacityValue.textContent =
      `${camsAirOpacityPercent}%`;
  }

  if (map.getLayer(CAMS_RUNTIME_CONFIG.layerId)) {
    map.setPaintProperty(
      CAMS_RUNTIME_CONFIG.layerId,
      'fill-opacity',
      camsAirOpacityPercent / 100,
    );
  }
}


function renderCamsAirOperational() {
  if (!camsAirOperational) return;

  const visible = Boolean(
    camsAirPayload
    && camsAirLayerVisible()
    && !camsAirErrorMessage
  );

  camsAirOperational.hidden = !visible;
  if (!visible) return;

  const view =
    camsFieldViewModel(camsAirPayload);

  if (camsAirValidTime) {
    camsAirValidTime.textContent =
      view.validTime
        ? (
          formatCurrentValidTime(
            view.validTime,
            localeForLanguage(currentLanguage),
          )
          + (
            Number.isFinite(view.leadHour)
              ? ` · +${view.leadHour} h`
              : ''
          )
        )
        : '—';
  }

  if (camsAirMin) {
    camsAirMin.textContent =
      formatCamsConcentration(view.minimum);
  }

  if (camsAirMean) {
    camsAirMean.textContent =
      formatCamsConcentration(view.mean);
  }

  if (camsAirMax) {
    camsAirMax.textContent =
      formatCamsConcentration(view.maximum);
  }

  if (camsAirUnits) {
    camsAirUnits.textContent = view.units;
  }

  if (camsAirLegendMin) {
    camsAirLegendMin.textContent =
      formatCamsConcentration(view.legendMin);
  }

  if (camsAirLegendMid) {
    camsAirLegendMid.textContent =
      formatCamsConcentration(view.legendMid);
  }

  if (camsAirLegendMax) {
    camsAirLegendMax.textContent =
      formatCamsConcentration(view.legendMax);
  }

  applyCamsAirOpacity();
}


function makeCamsAirPopupContent(properties) {
  const root = document.createElement('div');
  root.className =
    'ocean-current-popup cams-air-popup';

  const title = document.createElement('div');
  title.className =
    'ocean-current-popup__title';
  title.textContent =
    t(currentLanguage, 'air.popupTitle');

  root.append(title);

  const view =
    camsFieldViewModel(camsAirPayload);

  const rows = [
    [
      t(currentLanguage, 'air.value'),
      `${formatCamsConcentration(
        properties.value,
      )} ${view.units}`,
    ],
    [
      t(currentLanguage, 'air.pollutant'),
      view.pollutant,
    ],
    [
      t(currentLanguage, 'air.validTime'),
      view.validTime
        ? formatCurrentValidTime(
          view.validTime,
          localeForLanguage(currentLanguage),
        )
        : '—',
    ],
    [
      t(currentLanguage, 'air.forecastRun'),
      view.runTime
        ? (
          `${formatCurrentValidTime(
            view.runTime,
            localeForLanguage(currentLanguage),
          )}`
          + (
            Number.isFinite(view.leadHour)
              ? ` · +${view.leadHour} h`
              : ''
          )
        )
        : '—',
    ],
    [
      t(currentLanguage, 'air.model'),
      `CAMS ${view.model}`,
    ],
  ];

  for (const [label, value] of rows) {
    const row = document.createElement('div');
    row.className =
      'ocean-current-popup__row';

    const key = document.createElement('div');
    key.className =
      'ocean-current-popup__key';
    key.textContent = label;

    const valueElement =
      document.createElement('div');
    valueElement.className =
      'ocean-current-popup__value';
    valueElement.textContent = value;

    row.append(key, valueElement);
    root.append(row);
  }

  const disclaimer =
    document.createElement('div');

  disclaimer.className =
    'cams-air-popup__disclaimer';

  disclaimer.textContent =
    t(
      currentLanguage,
      'air.modelDisclaimer',
    );

  root.append(disclaimer);

  return root;
}


function installCamsAirLayer() {
  map.addSource(
    CAMS_RUNTIME_CONFIG.sourceId,
    {
      type: 'geojson',
      data: emptyFeatureCollection(),
    },
  );

  const beforeId =
    map.getLayer('monitor-events-glow')
      ? 'monitor-events-glow'
      : undefined;

  map.addLayer(
    {
      id: CAMS_RUNTIME_CONFIG.layerId,
      type: 'fill',
      source: CAMS_RUNTIME_CONFIG.sourceId,
      layout: {
        visibility: 'none',
      },
      paint: {
        'fill-color': '#3157d5',
        'fill-opacity':
          camsAirOpacityPercent / 100,
        'fill-outline-color':
          'rgba(255,255,255,0)',
      },
    },
    beforeId,
  );

  map.on(
    'mouseenter',
    CAMS_RUNTIME_CONFIG.layerId,
    () => {
      map.getCanvas().style.cursor =
        'pointer';
    },
  );

  map.on(
    'mouseleave',
    CAMS_RUNTIME_CONFIG.layerId,
    () => {
      map.getCanvas().style.cursor = '';
    },
  );

  map.on(
    'click',
    CAMS_RUNTIME_CONFIG.layerId,
    (event) => {
      if (
        driftSelectionActive
        || driftSelectionJustConsumed
      ) return;

      const feature =
        event.features?.[0];

      if (!feature) return;

      if (camsAirPopup) {
        camsAirPopup.remove();
      }

      camsAirPopup =
        new maplibregl.Popup({
          closeButton: true,
          closeOnClick: true,
          offset: 10,
        })
          .setLngLat(event.lngLat)
          .setDOMContent(
            makeCamsAirPopupContent(
              feature.properties ?? {},
            ),
          )
          .addTo(map);
    },
  );

  applyCamsAirOpacity();
}


function setCamsAirVisibility(visible) {
  if (map.getLayer(CAMS_RUNTIME_CONFIG.layerId)) {
    map.setLayoutProperty(
      CAMS_RUNTIME_CONFIG.layerId,
      'visibility',
      visible ? 'visible' : 'none',
    );
  }

  if (!visible && camsAirPopup) {
    camsAirPopup.remove();
    camsAirPopup = null;
  }

  renderCamsAirOperational();
}


async function refreshCamsAir() {
  if (
    !camsAirLayerVisible()
    || camsAirLoading
  ) return;

  camsAirLoading = true;
  camsAirErrorMessage = '';
  renderCamsAirStatus();

  try {
    const response =
      await fetch(
        `${CAMS_RUNTIME_CONFIG.endpoint}?pollutant=${camsAirPollutant}&stride=1`,
      );

    if (!response.ok) {
      let detail = String(response.status);

      try {
        const errorPayload =
          await response.json();

        detail =
          errorPayload.detail
          || detail;
      } catch {
        // Keep status.
      }

      throw new Error(detail);
    }

    camsAirPayload =
      await response.json();

    const source =
      map.getSource(
        CAMS_RUNTIME_CONFIG.sourceId,
      );

    if (source && camsAirPayload?.grid) {
      source.setData(
        buildCamsAirCellGeoJSON(
          camsAirPayload,
        ),
      );
    }

    if (map.getLayer(CAMS_RUNTIME_CONFIG.layerId)) {
      map.setPaintProperty(
        CAMS_RUNTIME_CONFIG.layerId,
        'fill-color',
        camsFillColorExpression(
          camsAirPayload,
        ),
      );
    }

    setCamsAirVisibility(true);
  } catch (error) {
    console.error(
      '[Black Sea Eco Monitor / CAMS]',
      error,
    );

    camsAirErrorMessage =
      error?.message || String(error);

    setCamsAirVisibility(false);
  } finally {
    camsAirLoading = false;
    renderCamsAirStatus();
  }
}


function renderCamsAirStatus() {
  if (!camsAirNote) return;

  camsAirNote.classList.toggle(
    'cams-air-note--loading',
    camsAirLoading,
  );

  camsAirNote.classList.toggle(
    'cams-air-note--error',
    Boolean(camsAirErrorMessage),
  );

  if (!camsAirLayerVisible()) {
    camsAirNote.textContent =
      t(currentLanguage, 'air.off');
  } else if (camsAirLoading) {
    camsAirNote.textContent =
      t(currentLanguage, 'air.loading');
  } else if (camsAirErrorMessage) {
    camsAirNote.textContent =
      t(
        currentLanguage,
        'air.error',
        {
          message:
            camsAirErrorMessage,
        },
      );
  } else if (camsAirPayload) {
    const view =
      camsFieldViewModel(camsAirPayload);

    camsAirNote.textContent =
      t(
        currentLanguage,
        'air.readyDetailed',
        {
          pollutant:
            view.pollutant,
          time:
            view.validTime
              ? formatCurrentValidTime(
                view.validTime,
                localeForLanguage(currentLanguage),
              )
              : '—',
        },
      );
  } else {
    camsAirNote.textContent =
      t(currentLanguage, 'air.off');
  }

  renderCamsAirOperational();
}


function windLayerVisible() {
  return Boolean(
    windToggle?.checked,
  );
}


function renderWindArrowSizeControl() {
  if (windArrowSizeSlider) {
    windArrowSizeSlider.value =
      String(
        windArrowSizePercent,
      );
  }

  if (windArrowSizeValue) {
    windArrowSizeValue.textContent =
      `${windArrowSizePercent}%`;
  }
}


function applyWindArrowSize() {
  renderWindArrowSizeControl();

  if (
    !map.getLayer(
      'weather-wind-arrows',
    )
  ) {
    return;
  }

  map.setLayoutProperty(
    'weather-wind-arrows',
    'icon-size',
    windArrowSizeExpression(
      windArrowSizePercent,
    ),
  );
}


function setWindLayerVisibility(
  visible,
) {
  const visibility =
    (
      visible
      && windModeShowsArrows()
    )
      ? 'visible'
      : 'none';

  if (
    map.getLayer(
      'weather-wind-arrows',
    )
  ) {
    map.setLayoutProperty(
      'weather-wind-arrows',
      'visibility',
      visibility,
    );
  }

  if (!visible) {
    windParticleEngine?.stop();

    if (windPopup) {
      windPopup.remove();
      windPopup = null;
    }
  }
}


function renderWindStatus() {
  renderCombinedFieldsHud();

  if (!windNote) return;

  windNote.classList.toggle(
    'weather-wind-note--loading',
    windLoading,
  );
  windNote.classList.toggle(
    'weather-wind-note--error',
    Boolean(
      windErrorMessage,
    ),
  );

  if (!windLayerVisible()) {
    windNote.textContent = t(
      currentLanguage,
      'weather.windOff',
    );
    return;
  }

  if (windLoading) {
    windNote.textContent = t(
      currentLanguage,
      'weather.windLoading',
    );
    return;
  }

  if (windErrorMessage) {
    windNote.textContent = t(
      currentLanguage,
      'weather.windError',
      {
        message:
          windErrorMessage,
      },
    );
    return;
  }

  if (windPayload) {
    windNote.textContent = t(
      currentLanguage,
      'weather.windReady',
      {
        time:
          formatCurrentValidTime(
            windPayload.valid_time,
            localeForLanguage(
              currentLanguage,
            ),
          ),
        count:
          windPayload.vector_count,
        run:
          formatCurrentValidTime(
            windPayload
              .forecast_reference_time,
            localeForLanguage(
              currentLanguage,
            ),
          ),
      },
    );
    return;
  }

  windNote.textContent = t(
    currentLanguage,
    'weather.windOff',
  );
}


function makeWindPopupContent(
  properties,
) {
  const root =
    document.createElement(
      'div',
    );

  root.className =
    'ocean-current-popup wind-popup';

  const title =
    document.createElement(
      'div',
    );

  title.className =
    'ocean-current-popup__title';

  title.textContent = t(
    currentLanguage,
    'weather.popupTitle',
  );

  root.append(title);

  const fromDegrees =
    Number(
      properties
        .direction_from_deg,
    );
  const toDegrees =
    Number(
      properties
        .direction_to_deg,
    );

  const sourceText =
    [
      'ECMWF IFS',
      ...(windPayload?.sources ?? []),
    ]
      .filter(Boolean)
      .join(' · ');

  const rows = [
    [
      t(
        currentLanguage,
        'weather.speed',
      ),
      formatWindSpeed(
        properties.speed,
      ),
    ],
    [
      t(
        currentLanguage,
        'weather.from',
      ),
      (
        Number.isFinite(
          fromDegrees,
        )
          ? (
            `${cardinalDirection(
              fromDegrees,
              currentLanguage,
            )} · `
            + `${fromDegrees.toFixed(0)}°`
          )
          : '—'
      ),
    ],
    [
      t(
        currentLanguage,
        'weather.to',
      ),
      (
        Number.isFinite(
          toDegrees,
        )
          ? (
            `${cardinalDirection(
              toDegrees,
              currentLanguage,
            )} · `
            + `${toDegrees.toFixed(0)}°`
          )
          : '—'
      ),
    ],
    [
      t(
        currentLanguage,
        'weather.components',
      ),
      (
        `u ${Number(
          properties.u,
        ).toFixed(2)} · `
        + `v ${Number(
          properties.v,
        ).toFixed(2)} m/s`
      ),
    ],
    [
      t(
        currentLanguage,
        'weather.modelTime',
      ),
      formatCurrentValidTime(
        windPayload?.valid_time,
        localeForLanguage(
          currentLanguage,
        ),
      ),
    ],
    [
      t(
        currentLanguage,
        'weather.forecastRun',
      ),
      formatCurrentValidTime(
        windPayload
          ?.forecast_reference_time,
        localeForLanguage(
          currentLanguage,
        ),
      ),
    ],
    [
      t(
        currentLanguage,
        'weather.source',
      ),
      sourceText || 'ECMWF IFS',
    ],
  ];

  for (
    const [
      keyText,
      valueText,
    ]
    of rows
  ) {
    const row =
      document.createElement(
        'div',
      );

    row.className =
      'ocean-current-popup__row';

    const key =
      document.createElement(
        'div',
      );

    key.className =
      'ocean-current-popup__key';
    key.textContent = keyText;

    const value =
      document.createElement(
        'div',
      );

    value.className =
      'ocean-current-popup__value';
    value.textContent =
      valueText;

    row.append(
      key,
      value,
    );

    root.append(row);
  }

  return root;
}


function installWindLayer() {
  if (
    !map.hasImage(
      'weather-wind-arrow',
    )
  ) {
    map.addImage(
      'weather-wind-arrow',
      createWindArrowImage(),
      {
        pixelRatio: 2,
      },
    );
  }

  map.addSource(
    'weather-wind',
    {
      type: 'geojson',
      data:
        emptyFeatureCollection(),
    },
  );

  map.addLayer({
    id: 'weather-wind-arrows',
    type: 'symbol',
    source: 'weather-wind',
    layout: {
      visibility: 'none',
      'icon-image':
        'weather-wind-arrow',
      'icon-size':
        windArrowSizeExpression(
          windArrowSizePercent,
        ),
      // IMPORTANT:
      // backend direction_to_deg is the physical direction
      // the air travels TO. Map arrows must use TO, not
      // meteorological FROM.
      'icon-rotate': [
        'get',
        'direction_to_deg',
      ],
      'icon-rotation-alignment':
        'map',
      'icon-pitch-alignment':
        'map',
      'icon-allow-overlap':
        true,
      'icon-ignore-placement':
        true,
      'icon-padding': 0,
    },
    paint: {
      'icon-opacity': [
        'interpolate',
        ['linear'],
        ['get', 'speed'],
        0, 0.58,
        2, 0.72,
        5, 0.88,
        10, 0.98,
        15, 1.0,
      ],
    },
  });

  applyWindArrowSize();

  map.on(
    'mouseenter',
    'weather-wind-arrows',
    () => {
      map.getCanvas()
        .style.cursor =
          'pointer';
    },
  );

  map.on(
    'mouseleave',
    'weather-wind-arrows',
    () => {
      map.getCanvas()
        .style.cursor = '';
    },
  );

  map.on(
    'click',
    'weather-wind-arrows',
    (event) => {
      if (
        driftSelectionActive
        || driftSelectionJustConsumed
      ) return;

      const feature =
        event.features?.[0];

      if (!feature) return;

      if (windPopup) {
        windPopup.remove();
      }

      windPopup =
        new maplibregl.Popup({
          closeButton: true,
          closeOnClick: true,
          offset: 10,
        })
          .setLngLat(
            feature.geometry
              .coordinates,
          )
          .setDOMContent(
            makeWindPopupContent(
              feature.properties
              ?? {},
            ),
          )
          .addTo(map);
    },
  );
}


async function refreshWind() {
  if (
    !windLayerVisible()
    || windLoading
  ) {
    return;
  }

  windLoading = true;
  windErrorMessage = '';
  renderWindStatus();

  try {
    const payload =
      await fetchWindField({
        stride:
          WIND_STRIDE,
      });

    windPayload = payload;

    if (windParticleEngine) {
      windParticleEngine.setField(
        payload,
      );
    }

    const source =
      map.getSource(
        'weather-wind',
      );

    if (source) {
      source.setData(
        windToFeatureCollection(
          payload,
        ),
      );
    }

    syncWindVisualization();
  } catch (error) {
    console.error(
      '[Black Sea Eco Monitor / wind]',
      error,
    );

    windErrorMessage =
      error.message;

    if (!windPayload) {
      setWindLayerVisibility(
        false,
      );
    }
  } finally {
    windLoading = false;
    renderWindStatus();
  }
}


for (
  const input
  of windDisplayModeInputs
) {
  input.addEventListener(
    'change',
    () => {
      if (!input.checked) {
        return;
      }

      windDisplayMode =
        normalizeWindDisplayMode(
          input.value,
        );

      window.localStorage.setItem(
        WIND_DISPLAY_MODE_STORAGE_KEY,
        windDisplayMode,
      );

      syncWindVisualization();
    },
  );
}


windParticleCountSlider
  ?.addEventListener(
    'input',
    () => {
      windParticleCount =
        normalizeWindParticleCount(
          windParticleCountSlider.value,
        );

      window.localStorage.setItem(
        WIND_PARTICLE_COUNT_STORAGE_KEY,
        String(
          windParticleCount,
        ),
      );

      windParticleEngine
        ?.setParticleCount(
          windParticleCount,
        );

      renderWindDisplayControls();
    },
  );


windParticleSpeedSlider
  ?.addEventListener(
    'input',
    () => {
      windParticleSpeedPercent =
        normalizeWindParticleSpeedPercent(
          windParticleSpeedSlider.value,
        );

      window.localStorage.setItem(
        WIND_PARTICLE_SPEED_STORAGE_KEY,
        String(
          windParticleSpeedPercent,
        ),
      );

      windParticleEngine
        ?.setSpeedPercent(
          windParticleSpeedPercent,
        );

      renderWindDisplayControls();
    },
  );


windParticleTrailSlider
  ?.addEventListener(
    'input',
    () => {
      windParticleTrailPercent =
        normalizeWindParticleTrailPercent(
          windParticleTrailSlider.value,
        );

      window.localStorage.setItem(
        WIND_PARTICLE_TRAIL_STORAGE_KEY,
        String(
          windParticleTrailPercent,
        ),
      );

      windParticleEngine
        ?.setTrailPercent(
          windParticleTrailPercent,
        );

      renderWindDisplayControls();
    },
  );


windParticleSizeSlider
  ?.addEventListener(
    'input',
    () => {
      windParticleSizePercent =
        normalizeWindParticleSizePercent(
          windParticleSizeSlider.value,
        );

      window.localStorage.setItem(
        WIND_PARTICLE_SIZE_STORAGE_KEY,
        String(
          windParticleSizePercent,
        ),
      );

      windParticleEngine
        ?.setSizePercent(
          windParticleSizePercent,
        );

      renderWindDisplayControls();
    },
  );


renderWindDisplayControls();


windArrowSizeSlider
  ?.addEventListener(
    'input',
    () => {
      windArrowSizePercent =
        normalizeWindArrowSizePercent(
          windArrowSizeSlider.value,
        );

      window.localStorage
        .setItem(
          WIND_ARROW_SIZE_STORAGE_KEY,
          String(
            windArrowSizePercent,
          ),
        );

      applyWindArrowSize();
    },
  );


renderWindArrowSizeControl();


camsAirOpacitySlider
  ?.addEventListener(
    'input',
    () => {
      camsAirOpacityPercent =
        normalizeCamsOpacityPercent(
          camsAirOpacitySlider.value,
        );

      window.localStorage.setItem(
        CAMS_AIR_OPACITY_STORAGE_KEY,
        String(camsAirOpacityPercent),
      );

      applyCamsAirOpacity();
    },
  );


camsAirToggle?.addEventListener(
  'change',
  () => {
    if (camsAirToggle.checked) {
      void refreshCamsAir();
    } else {
      setCamsAirVisibility(false);
      renderCamsAirStatus();
    }
  },
);

camsAirPollutantSelect?.addEventListener(
  'change',
  () => {
    camsAirPollutant = camsAirPollutantSelect.value;
    if (camsAirToggle?.checked) {
      void refreshCamsAir();
    }
  },
);

windToggle?.addEventListener(
  'change',
  () => {
    if (windLayerVisible()) {
      syncWindVisualization();
      void refreshWind();
    } else {
      syncWindVisualization();
      renderWindStatus();
    }
  },
);


document.addEventListener(
  'visibilitychange',
  () => {
    syncCurrentVisualization();
    syncWindVisualization();
  },
);


map.on(
  'movestart',
  () => {
    mapIsMoving = true;
    currentParticleEngine?.stop();
    windParticleEngine?.stop();
  },
);


map.on(
  'move',
  () => {
    currentParticleEngine?.clear();
    windParticleEngine?.clear();
  },
);


map.on(
  'moveend',
  () => {
    mapIsMoving = false;
    currentParticleEngine?.resize();
    windParticleEngine?.resize();
    syncCurrentVisualization();
    syncWindVisualization();
  },
);


map.on(
  'resize',
  () => {
    currentParticleEngine?.resize();
    windParticleEngine?.resize();
  },
);


function satelliteLayerVisible() {
  return Boolean(satelliteToggle?.checked);
}

function setSatelliteLayerVisibility(visible) {
  const visibility = visible
    ? 'visible'
    : 'none';

  for (const layerId of [
    'satellite-candidates-fill',
    'satellite-candidates-line',
  ]) {
    if (map.getLayer(layerId)) {
      map.setLayoutProperty(
        layerId,
        'visibility',
        visibility,
      );
    }
  }

  if (!visible && satellitePopup) {
    satellitePopup.remove();
    satellitePopup = null;
  }
}

function renderSatelliteStatus() {
  if (!satelliteNote) return;

  satelliteNote.classList.toggle(
    'satellite-layer-note--loading',
    satelliteCandidatesLoading,
  );
  satelliteNote.classList.toggle(
    'satellite-layer-note--error',
    Boolean(satelliteCandidatesErrorMessage),
  );

  if (!satelliteLayerVisible()) {
    satelliteNote.textContent = t(
      currentLanguage,
      'satellite.off',
    );
    return;
  }

  if (satelliteCandidatesLoading) {
    satelliteNote.textContent = t(
      currentLanguage,
      'satellite.loading',
    );
    return;
  }

  if (satelliteCandidatesErrorMessage) {
    satelliteNote.textContent = t(
      currentLanguage,
      'satellite.error',
      {
        message: satelliteCandidatesErrorMessage,
      },
    );
    return;
  }

  satelliteNote.textContent = t(
    currentLanguage,
    'satellite.ready',
    {
      count: satelliteCandidatesPayload?.features?.length ?? 0,
    },
  );
}

function prepareDriftFromSatelliteCandidate(
  feature,
) {
  const seed = satelliteCandidateSeed(feature);

  if (!seed) {
    return;
  }

  driftSelectionActive = false;
  driftSelectionJustConsumed = false;
  driftSeed = {
    longitude: seed.longitude,
    latitude: seed.latitude,
  };
  driftSeedSourceEventId = null;
  driftForecastSourceEventId = null;
  driftSeedSourceKind = seed.sourceKind;
  driftSeedSourceId = seed.sourceId;
  driftForecastSourceKind = null;
  driftForecastSourceId = null;
  driftPayload = null;
  driftErrorMessage = '';

  clearImpactScreening();

  map.getCanvas().style.cursor = '';
  renderDriftMap();
  renderDriftControls();
  refreshSelectedPanel();
}


function makeSatellitePopupContent(feature) {
  const vm = satelliteCandidateViewModel(feature);
  const root = makeElement(
    'div',
    'satellite-candidate-popup',
  );

  root.append(
    makeElement(
      'div',
      'satellite-candidate-popup__title',
      t(currentLanguage, 'satellite.popupTitle'),
    ),
  );

  const rows = [
    [
      t(currentLanguage, 'satellite.area'),
      vm.areaKm2 == null
        ? '—'
        : `${vm.areaKm2.toFixed(5)} km²`,
    ],
    [
      t(currentLanguage, 'satellite.meanVv'),
      vm.meanVvDb == null
        ? '—'
        : `${vm.meanVvDb.toFixed(2)} dB`,
    ],
    [
      t(currentLanguage, 'satellite.threshold'),
      vm.thresholdDb == null
        ? '—'
        : `${vm.thresholdDb.toFixed(1)} dB`,
    ],
    [
      t(currentLanguage, 'satellite.reviewStatus'),
      vm.reviewStatus,
    ],
  ];

  for (const [label, value] of rows) {
    const row = makeElement(
      'div',
      'satellite-candidate-popup__row',
    );
    row.append(
      makeElement(
        'div',
        'satellite-candidate-popup__key',
        label,
      ),
      makeElement(
        'div',
        'satellite-candidate-popup__value',
        value,
      ),
    );
    root.append(row);
  }

  root.append(
    makeElement(
      'div',
      'satellite-candidate-popup__disclaimer',
      t(currentLanguage, 'satellite.disclaimer'),
    ),
  );

  const candidateSeed = satelliteCandidateSeed(feature);

  if (candidateSeed) {
    const seedButton = makeWorkflowButton(
      t(currentLanguage, 'satellite.useAsSeed'),
      'workflow-button workflow-button--secondary',
    );

    seedButton.addEventListener(
      'click',
      () => {
        prepareDriftFromSatelliteCandidate(feature);

        if (satellitePopup) {
          satellitePopup.remove();
          satellitePopup = null;
        }
      },
    );

    root.append(seedButton);
  }

  return root;
}

function installSatelliteLayer() {
  map.addSource(
    'satellite-candidates',
    {
      type: 'geojson',
      data: emptyFeatureCollection(),
    },
  );

  map.addLayer({
    id: 'satellite-candidates-fill',
    type: 'fill',
    source: 'satellite-candidates',
    layout: {
      visibility: 'none',
    },
    paint: {
      'fill-color': '#c77dff',
      'fill-opacity': 0.22,
    },
  });

  map.addLayer({
    id: 'satellite-candidates-line',
    type: 'line',
    source: 'satellite-candidates',
    layout: {
      visibility: 'none',
    },
    paint: {
      'line-color': '#e0aaff',
      'line-width': 2.2,
      'line-opacity': 0.95,
    },
  });

  map.on(
    'mouseenter',
    'satellite-candidates-fill',
    () => {
      map.getCanvas().style.cursor = 'pointer';
    },
  );

  map.on(
    'mouseleave',
    'satellite-candidates-fill',
    () => {
      map.getCanvas().style.cursor = '';
    },
  );

  map.on(
    'click',
    'satellite-candidates-fill',
    (event) => {
      if (
        driftSelectionActive
        || driftSelectionJustConsumed
      ) return;

      const feature = event.features?.[0];

      if (!feature) return;

      if (satellitePopup) {
        satellitePopup.remove();
      }

      satellitePopup = new maplibregl.Popup({
        closeButton: true,
        closeOnClick: true,
        offset: 10,
      })
        .setLngLat(event.lngLat)
        .setDOMContent(
          makeSatellitePopupContent(feature),
        )
        .addTo(map);
    },
  );
}

async function refreshSatelliteCandidates() {
  if (
    !satelliteLayerVisible()
    || satelliteCandidatesLoading
  ) {
    return;
  }

  satelliteCandidatesLoading = true;
  satelliteCandidatesErrorMessage = '';
  renderSatelliteStatus();

  try {
    const payload = await fetchSatelliteCandidates();

    satelliteCandidatesPayload = payload;

    setGeoJSONSourceData(
      'satellite-candidates',
      payload,
    );

    if (payload.features.length) {
  const bounds = new maplibregl.LngLatBounds();

  for (const feature of payload.features) {
    const coords = feature.geometry.coordinates.flat(10);

    for (let i = 0; i < coords.length; i += 2) {
      bounds.extend([
        coords[i],
        coords[i + 1],
      ]);
    }
  }

  map.fitBounds(bounds, {
    padding: 120,
    maxZoom: 13,
    duration: 1200,
  });
}

    setSatelliteLayerVisibility(true);
  } catch (error) {
    console.error(
      '[Black Sea Eco Monitor / satellite]',
      error,
    );
    satelliteCandidatesErrorMessage =
      error?.message || String(error);

    if (!satelliteCandidatesPayload) {
      setSatelliteLayerVisibility(false);
    }
  } finally {
    satelliteCandidatesLoading = false;
    renderSatelliteStatus();
  }
}

satelliteToggle?.addEventListener(
  'change',
  () => {
    if (satelliteLayerVisible()) {
      setSatelliteLayerVisibility(true);
      void refreshSatelliteCandidates();
    } else {
      setSatelliteLayerVisibility(false);
      renderSatelliteStatus();
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
  renderCurrentsStatus();
  renderCurrentDisplayControls();
  renderWindStatus();
  renderCamsAirStatus();
  renderLongTaskUX();
  renderDriftControls();
  renderSatelliteStatus();

  if (currentsPopup) {
    currentsPopup.remove();
    currentsPopup = null;
  }

  if (windPopup) {
    windPopup.remove();
    windPopup = null;
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
  driftSeedSourceEventId = null;
  driftForecastSourceEventId = null;
  driftSeedSourceKind = 'manual';
  driftSeedSourceId = null;
  driftForecastSourceKind = null;
  driftForecastSourceId = null;
  clearImpactScreening();
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
  refreshSelectedPanel();
});


map.on('load', () => {
  installRegionalFocus(map);
  installSatelliteLayer();
  installEventLayer();
  installCurrentLayer();
  installWindLayer();
   installCamsAirLayer();
   installTropomiSatelliteLayer(map);
   installGeosCfAirLayer(map);
  installDriftLayer();
  installImpactLayer();
  mountFinalEvidencePanel();
  renderCurrentsStatus();
  renderCurrentDisplayControls();
  renderWindStatus();
  renderWindDisplayControls();
  renderCamsAirStatus();
  renderDriftControls();
  renderSatelliteStatus();

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

  window.setInterval(
    () => {
      if (windLayerVisible()) {
        void refreshWind();
      }
    },
    WIND_REFRESH_INTERVAL_MS,
  );
});
