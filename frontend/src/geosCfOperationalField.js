const SOURCE_ID = 'geos-cf-air-quality';
const LAYER_ID = 'geos-cf-air-quality-fill';
const OPACITY_KEY = 'black-sea-eco-monitor.geos-cf-opacity';

export const GEOS_CF_RUNTIME_CONFIG = {
  fieldEndpoint: '/air/geos-cf-field',
  crosscheckEndpoint: '/air/model-crosscheck',
  defaultProduct: 'pm25',
  defaultTimeIndex: 0,
  defaultStride: 1,
};

const PRODUCT_LABELS = {
  pm25: 'PM2.5',
  pm10: 'PM10',
};

const COLORS = [
  '#40539C',
  '#2A86B8',
  '#45B3A0',
  '#E5C85E',
  '#D36B58',
];

function finiteNumber(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export function inferEdges(centres) {
  const values = Array.from(centres || [], Number);
  if (!values.length) return [];
  if (values.length === 1) {
    return [values[0] - 0.125, values[0] + 0.125];
  }

  const edges = [];
  edges.push(values[0] - (values[1] - values[0]) / 2);
  for (let i = 1; i < values.length; i += 1) {
    edges.push((values[i - 1] + values[i]) / 2);
  }
  const last = values.length - 1;
  edges.push(values[last] + (values[last] - values[last - 1]) / 2);
  return edges;
}

export function buildGeosCfCellCollection(field) {
  const longitude = Array.isArray(field?.longitude) ? field.longitude : [];
  const latitude = Array.isArray(field?.latitude) ? field.latitude : [];
  const values = Array.isArray(field?.values) ? field.values : [];

  const lonEdges = inferEdges(longitude);
  const latEdges = inferEdges(latitude);
  const features = [];

  for (let row = 0; row < latitude.length; row += 1) {
    const rowValues = Array.isArray(values[row]) ? values[row] : [];
    for (let col = 0; col < longitude.length; col += 1) {
      const value = finiteNumber(rowValues[col]);
      if (value === null) continue;

      features.push({
        type: 'Feature',
        properties: {
          value,
          row,
          col,
        },
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [lonEdges[col], latEdges[row]],
            [lonEdges[col + 1], latEdges[row]],
            [lonEdges[col + 1], latEdges[row + 1]],
            [lonEdges[col], latEdges[row + 1]],
            [lonEdges[col], latEdges[row]],
          ]],
        },
      });
    }
  }

  return {
    type: 'FeatureCollection',
    features,
  };
}

export function robustStops(field) {
  const stats = field?.statistics || {};
  const raw = [
    stats.p05,
    stats.p25,
    stats.p50,
    stats.p75,
    stats.p95,
  ]
    .map(finiteNumber)
    .filter((value) => value !== null);

  if (raw.length !== 5) {
    const min = finiteNumber(stats.min) ?? 0;
    const max = finiteNumber(stats.max) ?? (min + 1);
    const step = (max - min || 1) / 4;
    return [0, 1, 2, 3, 4].map((index) => min + step * index);
  }

  const result = raw.slice();
  for (let i = 1; i < result.length; i += 1) {
    if (result[i] <= result[i - 1]) {
      result[i] = result[i - 1] + Number.EPSILON;
    }
  }
  return result;
}

export function formatFieldValue(value, units = 'µg/m³') {
  const number = finiteNumber(value);
  if (number === null) return '—';
  return `${number.toFixed(2)} ${units}`;
}

export function buildCrosscheckViewModel(payload) {
  const metrics = payload?.metrics || {};
  const spatial = payload?.spatial_alignment || {};
  const time = payload?.time_alignment || {};

  return {
    timeGapMinutes: finiteNumber(time.absolute_gap_minutes),
    coveragePercent: finiteNumber(spatial.comparison_coverage_percent),
    comparedPoints: finiteNumber(spatial.compared_points),
    geosMean: finiteNumber(metrics.geos_mean),
    camsMean: finiteNumber(metrics.cams_mean),
    bias: finiteNumber(metrics.bias_geos_minus_cams),
    mae: finiteNumber(metrics.mae),
    rmse: finiteNumber(metrics.rmse),
    pearsonR: finiteNumber(metrics.pearson_r),
    classification:
      payload?.semantics?.agreement_classification || 'not_calibrated',
  };
}

function language() {
  return (document.documentElement.lang || 'ru').toLowerCase().startsWith('ru')
    ? 'ru'
    : 'en';
}

function copy() {
  return language() === 'ru'
    ? {
        title: 'NASA GEOS-CF v2',
        subtitle: 'Независимый модельный прогноз состава атмосферы',
        layer: 'Слой GEOS-CF',
        product: 'Продукт',
        run: 'Запуск',
        valid: 'Модельное время',
        age: 'Возраст запуска',
        opacity: 'Прозрачность',
        selected: 'Выбранная ячейка',
        loading: 'Загрузка GEOS-CF…',
        ready: 'GEOS-CF поле загружено',
        off: 'Слой выключен',
        error: 'GEOS-CF недоступен',
        click: 'Кликните по ячейке для точного модельного значения',
        disclaimer:
          'Исследовательский модельный прогноз NASA. Не станционное измерение и не ground truth.',
        crossTitle: 'Сравнение моделей',
        crossSubtitle: 'CAMS Europe ↔ NASA GEOS-CF',
        compare: 'Сравнить CAMS ↔ GEOS-CF',
        comparing: 'Сравнение моделей…',
        crossReady: 'Метрики рассчитаны',
        crossError: 'Сравнение недоступно',
        timeGap: 'Разрыв времени',
        coverage: 'Покрытие',
        geosMean: 'GEOS mean',
        camsMean: 'CAMS mean',
        bias: 'Bias GEOS−CAMS',
        mae: 'MAE',
        rmse: 'RMSE',
        pearson: 'Pearson r',
        uncalibrated:
          'Порог agreement/disagreement не калиброван. Ни одна модель не считается ground truth.',
        min: 'MIN',
        mean: 'MEAN',
        max: 'MAX',
      }
    : {
        title: 'NASA GEOS-CF v2',
        subtitle: 'Independent atmospheric-composition model forecast',
        layer: 'GEOS-CF layer',
        product: 'Product',
        run: 'Run',
        valid: 'Valid time',
        age: 'Run age',
        opacity: 'Opacity',
        selected: 'Selected cell',
        loading: 'Loading GEOS-CF…',
        ready: 'GEOS-CF field loaded',
        off: 'Layer off',
        error: 'GEOS-CF unavailable',
        click: 'Click a cell for the exact model value',
        disclaimer:
          'NASA research model forecast. Not a station measurement and not ground truth.',
        crossTitle: 'Model cross-check',
        crossSubtitle: 'CAMS Europe ↔ NASA GEOS-CF',
        compare: 'Compare CAMS ↔ GEOS-CF',
        comparing: 'Comparing models…',
        crossReady: 'Metrics calculated',
        crossError: 'Cross-check unavailable',
        timeGap: 'Time gap',
        coverage: 'Coverage',
        geosMean: 'GEOS mean',
        camsMean: 'CAMS mean',
        bias: 'Bias GEOS−CAMS',
        mae: 'MAE',
        rmse: 'RMSE',
        pearson: 'Pearson r',
        uncalibrated:
          'Agreement/disagreement threshold is not calibrated. Neither model is treated as ground truth.',
        min: 'MIN',
        mean: 'MEAN',
        max: 'MAX',
      };
}

function createPanel(host) {
  host.innerHTML = `
    <div class="geos-cf-card">
      <div class="geos-cf-card__head">
        <div>
          <div class="geos-cf-card__title" data-geos-copy="title"></div>
          <div class="geos-cf-card__subtitle" data-geos-copy="subtitle"></div>
        </div>
        <label class="geos-cf-toggle">
          <span data-geos-copy="layer"></span>
          <input id="geos-cf-layer-toggle" type="checkbox" />
        </label>
      </div>

      <label class="geos-cf-field">
        <span data-geos-copy="product"></span>
        <select id="geos-cf-product">
          ${Object.entries(PRODUCT_LABELS)
            .map(([value, label]) => `<option value="${value}">${label}</option>`)
            .join('')}
        </select>
      </label>

      <div class="geos-cf-metrics">
        <div><span data-geos-copy="min"></span><strong id="geos-cf-min">—</strong></div>
        <div><span data-geos-copy="mean"></span><strong id="geos-cf-mean">—</strong></div>
        <div><span data-geos-copy="max"></span><strong id="geos-cf-max">—</strong></div>
      </div>

      <div class="geos-cf-legend">
        <div class="geos-cf-legend__bar"></div>
        <div class="geos-cf-legend__labels">
          <span id="geos-cf-legend-min">—</span>
          <span id="geos-cf-legend-mid">—</span>
          <span id="geos-cf-legend-max">—</span>
        </div>
      </div>

      <div class="geos-cf-meta">
        <div><span data-geos-copy="run"></span><strong id="geos-cf-run">—</strong></div>
        <div><span data-geos-copy="valid"></span><strong id="geos-cf-valid">—</strong></div>
        <div><span data-geos-copy="age"></span><strong id="geos-cf-age">—</strong></div>
      </div>

      <label class="geos-cf-opacity">
        <span data-geos-copy="opacity"></span>
        <input id="geos-cf-opacity" type="range" min="20" max="90" step="5" />
        <strong id="geos-cf-opacity-value">—</strong>
      </label>

      <div class="geos-cf-selected">
        <span data-geos-copy="selected"></span>
        <strong id="geos-cf-selected-value">—</strong>
      </div>

      <div class="geos-cf-hint" data-geos-copy="click"></div>
      <div class="geos-cf-status" id="geos-cf-status"></div>
      <div class="geos-cf-disclaimer" data-geos-copy="disclaimer"></div>
    </div>

    <div class="geos-crosscheck-card">
      <div class="geos-crosscheck-card__title" data-geos-copy="crossTitle"></div>
      <div class="geos-crosscheck-card__subtitle" data-geos-copy="crossSubtitle"></div>

      <button id="geos-crosscheck-run" class="geos-crosscheck-button" type="button">
        <span data-geos-copy="compare"></span>
      </button>

      <div class="geos-crosscheck-status" id="geos-crosscheck-status"></div>

      <div class="geos-crosscheck-grid">
        <div><span data-geos-copy="timeGap"></span><strong id="geos-cross-time-gap">—</strong></div>
        <div><span data-geos-copy="coverage"></span><strong id="geos-cross-coverage">—</strong></div>
        <div><span data-geos-copy="geosMean"></span><strong id="geos-cross-geos-mean">—</strong></div>
        <div><span data-geos-copy="camsMean"></span><strong id="geos-cross-cams-mean">—</strong></div>
        <div><span data-geos-copy="bias"></span><strong id="geos-cross-bias">—</strong></div>
        <div><span data-geos-copy="mae"></span><strong id="geos-cross-mae">—</strong></div>
        <div><span data-geos-copy="rmse"></span><strong id="geos-cross-rmse">—</strong></div>
        <div><span data-geos-copy="pearson"></span><strong id="geos-cross-pearson">—</strong></div>
      </div>

      <div class="geos-crosscheck-note" data-geos-copy="uncalibrated"></div>
    </div>
  `;
}

function applyCopy(host) {
  const strings = copy();
  host.querySelectorAll('[data-geos-copy]').forEach((element) => {
    const key = element.dataset.geosCopy;
    if (strings[key] != null) element.textContent = strings[key];
  });
}

function storedOpacity() {
  const raw = localStorage.getItem(OPACITY_KEY);
  if (raw == null || raw === '') return 55;
  const number = Number(raw);
  if (!Number.isFinite(number)) return 55;
  return Math.max(20, Math.min(90, number));
}

function fillExpression(stops) {
  const expression = ['interpolate', ['linear'], ['get', 'value']];
  stops.forEach((stop, index) => {
    expression.push(stop, COLORS[index]);
  });
  return expression;
}

function ensureLayer(map, collection, stops, opacity) {
  if (!map.getSource(SOURCE_ID)) {
    map.addSource(SOURCE_ID, {
      type: 'geojson',
      data: collection,
    });
  } else {
    map.getSource(SOURCE_ID).setData(collection);
  }

  if (!map.getLayer(LAYER_ID)) {
    const beforeId = map.getLayer('monitor-events-glow')
      ? 'monitor-events-glow'
      : undefined;

    map.addLayer(
      {
        id: LAYER_ID,
        type: 'fill',
        source: SOURCE_ID,
        paint: {
          'fill-color': fillExpression(stops),
          'fill-opacity': opacity / 100,
          'fill-outline-color': 'rgba(255,255,255,0.05)',
        },
      },
      beforeId,
    );
  } else {
    map.setPaintProperty(LAYER_ID, 'fill-color', fillExpression(stops));
    map.setPaintProperty(LAYER_ID, 'fill-opacity', opacity / 100);
  }
}

function formatTimestamp(value) {
  if (!value) return '—';
  return String(value).replace('T', ' ').replace('+00:00', ' UTC').replace('Z', ' UTC');
}

function metricText(value, decimals = 2, suffix = '') {
  const number = finiteNumber(value);
  if (number === null) return '—';
  return `${number.toFixed(decimals)}${suffix}`;
}

function updateFieldMetrics(host, field) {
  const units = field.units || '';
  const stats = field.statistics || {};

  host.querySelector('#geos-cf-min').textContent =
    formatFieldValue(stats.min, units);
  host.querySelector('#geos-cf-mean').textContent =
    formatFieldValue(stats.mean, units);
  host.querySelector('#geos-cf-max').textContent =
    formatFieldValue(stats.max, units);

  host.querySelector('#geos-cf-legend-min').textContent =
    metricText(stats.p05, 2);
  host.querySelector('#geos-cf-legend-mid').textContent =
    metricText(stats.p50, 2);
  host.querySelector('#geos-cf-legend-max').textContent =
    metricText(stats.p95, 2);

  host.querySelector('#geos-cf-run').textContent =
    formatTimestamp(field.run_time);
  host.querySelector('#geos-cf-valid').textContent =
    formatTimestamp(field.valid_time);

  const runAge = finiteNumber(field.freshness?.run_age_hours);
  host.querySelector('#geos-cf-age').textContent =
    runAge === null ? '—' : `${runAge.toFixed(1)} h`;
}

function updateCrosscheckMetrics(host, payload) {
  const view = buildCrosscheckViewModel(payload);
  const units = payload.units || 'µg/m³';

  host.querySelector('#geos-cross-time-gap').textContent =
    metricText(view.timeGapMinutes, 1, ' min');
  host.querySelector('#geos-cross-coverage').textContent =
    metricText(view.coveragePercent, 1, '%');
  host.querySelector('#geos-cross-geos-mean').textContent =
    formatFieldValue(view.geosMean, units);
  host.querySelector('#geos-cross-cams-mean').textContent =
    formatFieldValue(view.camsMean, units);
  host.querySelector('#geos-cross-bias').textContent =
    formatFieldValue(view.bias, units);
  host.querySelector('#geos-cross-mae').textContent =
    formatFieldValue(view.mae, units);
  host.querySelector('#geos-cross-rmse').textContent =
    formatFieldValue(view.rmse, units);
  host.querySelector('#geos-cross-pearson').textContent =
    metricText(view.pearsonR, 3);
}

export function installGeosCfAirLayer(map) {
  const host = document.getElementById('geos-cf-air-root');
  if (!host || !map) return null;

  createPanel(host);
  applyCopy(host);

  const toggle = host.querySelector('#geos-cf-layer-toggle');
  const product = host.querySelector('#geos-cf-product');
  const opacity = host.querySelector('#geos-cf-opacity');
  const opacityValue = host.querySelector('#geos-cf-opacity-value');
  const selectedValue = host.querySelector('#geos-cf-selected-value');
  const status = host.querySelector('#geos-cf-status');
  const crossStatus = host.querySelector('#geos-crosscheck-status');
  const crossButton = host.querySelector('#geos-crosscheck-run');

  let activeField = null;
  let fieldRequestSerial = 0;
  let crossRequestSerial = 0;

  const initialOpacity = storedOpacity();
  opacity.value = String(initialOpacity);
  opacityValue.textContent = `${initialOpacity}%`;

  async function refreshField() {
    const serial = ++fieldRequestSerial;
    status.textContent = copy().loading;

    const params = new URLSearchParams({
      product: product.value,
      time_index: String(GEOS_CF_RUNTIME_CONFIG.defaultTimeIndex),
      stride: String(GEOS_CF_RUNTIME_CONFIG.defaultStride),
    });

    try {
      const response = await fetch(
        `${GEOS_CF_RUNTIME_CONFIG.fieldEndpoint}?${params.toString()}`,
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const field = await response.json();
      if (serial !== fieldRequestSerial) return;

      const collection = buildGeosCfCellCollection(field);
      if (!collection.features.length) {
        throw new Error('No valid GEOS-CF cells');
      }

      activeField = field;
      selectedValue.textContent = '—';

      ensureLayer(
        map,
        collection,
        robustStops(field),
        Number(opacity.value),
      );
      map.setLayoutProperty(LAYER_ID, 'visibility', 'visible');
      updateFieldMetrics(host, field);
      status.textContent = copy().ready;
    } catch (error) {
      console.error('GEOS-CF field error:', error);
      status.textContent = copy().error;
    }
  }

  async function runCrosscheck() {
    const serial = ++crossRequestSerial;
    const strings = copy();

    crossButton.disabled = true;
    crossStatus.textContent = strings.comparing;

    const params = new URLSearchParams({
      product: product.value,
      geos_time_index: String(GEOS_CF_RUNTIME_CONFIG.defaultTimeIndex),
      geos_stride: '1',
      cams_stride: '1',
      max_time_gap_minutes: '45',
    });

    try {
      const response = await fetch(
        `${GEOS_CF_RUNTIME_CONFIG.crosscheckEndpoint}?${params.toString()}`,
      );
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new Error(payload?.detail || `HTTP ${response.status}`);
      }

      const payload = await response.json();
      if (serial !== crossRequestSerial) return;

      updateCrosscheckMetrics(host, payload);
      crossStatus.textContent = strings.crossReady;
    } catch (error) {
      console.error('CAMS/GEOS-CF cross-check error:', error);
      crossStatus.textContent = `${strings.crossError}: ${error.message}`;
    } finally {
      if (serial === crossRequestSerial) {
        crossButton.disabled = false;
      }
    }
  }

  toggle.addEventListener('change', () => {
    if (!toggle.checked) {
      if (map.getLayer(LAYER_ID)) {
        map.setLayoutProperty(LAYER_ID, 'visibility', 'none');
      }
      status.textContent = copy().off;
      return;
    }
    refreshField();
  });

  product.addEventListener('change', () => {
    crossStatus.textContent = '';
    host.querySelectorAll('.geos-crosscheck-grid strong').forEach((element) => {
      element.textContent = '—';
    });
    if (toggle.checked) refreshField();
  });

  opacity.addEventListener('input', () => {
    const value = Number(opacity.value);
    opacityValue.textContent = `${value}%`;
    localStorage.setItem(OPACITY_KEY, String(value));
    if (map.getLayer(LAYER_ID)) {
      map.setPaintProperty(LAYER_ID, 'fill-opacity', value / 100);
    }
  });

  crossButton.addEventListener('click', runCrosscheck);

  map.on('click', LAYER_ID, (event) => {
    const feature = event.features?.[0];
    if (!feature || !activeField) return;
    selectedValue.textContent = formatFieldValue(
      feature.properties?.value,
      activeField.units,
    );
  });

  map.on('mouseenter', LAYER_ID, () => {
    map.getCanvas().style.cursor = 'crosshair';
  });

  map.on('mouseleave', LAYER_ID, () => {
    map.getCanvas().style.cursor = '';
  });

  const observer = new MutationObserver(() => {
    applyCopy(host);
    if (!toggle.checked) status.textContent = copy().off;
    else if (activeField) status.textContent = copy().ready;
  });
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['lang'],
  });

  status.textContent = copy().off;

  return {
    refreshField,
    runCrosscheck,
    destroy() {
      observer.disconnect();
    },
  };
}
