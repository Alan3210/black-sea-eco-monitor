const SOURCE_ID = 'tropomi-air-quality';
const LAYER_ID = 'tropomi-air-quality-fill';
const OPACITY_KEY = 'black-sea-eco-monitor.tropomi-opacity';

export const TROPOMI_RUNTIME_CONFIG = {
  endpoint: '/air/satellite-field',
  defaultProduct: 'no2',
  defaultStride: 2,
  lookbackDays: 7,
};

const PRODUCT_LABELS = {
  no2: 'NO₂',
  so2: 'SO₂',
  co: 'CO',
  o3: 'O₃',
  ch4: 'CH₄',
  hcho: 'HCHO',
  aer_ai_340_380: 'AER AI 340/380',
  aer_ai_354_388: 'AER AI 354/388',
};

const COLORS = [
  '#31498F',
  '#2B8BC6',
  '#46B7A9',
  '#E6C85A',
  '#D76A55',
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
    return [values[0] - 0.025, values[0] + 0.025];
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

export function buildTropomiCellCollection(field) {
  const longitude = Array.isArray(field?.longitude) ? field.longitude : [];
  const latitude = Array.isArray(field?.latitude) ? field.latitude : [];
  const values = Array.isArray(field?.values) ? field.values : [];

  const lonEdges = inferEdges(longitude);
  const latEdges = inferEdges(latitude);
  const features = [];

  for (let row = 0; row < latitude.length; row += 1) {
    const rowValues = Array.isArray(values[row]) ? values[row] : [];
    for (let col = 0; col < longitude.length; col += 1) {
      const rawValue = finiteNumber(rowValues[col]);
      if (rawValue === null) continue;

      features.push({
        type: 'Feature',
        properties: {
          value: rawValue,
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

export function productDisplayMeta(product, units) {
  if (units === 'mol/m^2') {
    return {
      factor: 1e6,
      unit: 'µmol/m²',
      decimals: 2,
    };
  }
  if (units === 'ppb') {
    return {
      factor: 1,
      unit: 'ppb',
      decimals: 1,
    };
  }
  return {
    factor: 1,
    unit: product?.startsWith('aer_ai_') ? 'index' : (units || ''),
    decimals: 3,
  };
}

export function formatSatelliteValue(value, product, units) {
  const number = finiteNumber(value);
  if (number === null) return '—';
  const meta = productDisplayMeta(product, units);
  return `${(number * meta.factor).toFixed(meta.decimals)} ${meta.unit}`.trim();
}

function displayNumber(value, product, units) {
  const number = finiteNumber(value);
  if (number === null) return '—';
  const meta = productDisplayMeta(product, units);
  return (number * meta.factor).toFixed(meta.decimals);
}

function language() {
  return (document.documentElement.lang || 'ru').toLowerCase().startsWith('ru')
    ? 'ru'
    : 'en';
}

function copy() {
  return language() === 'ru'
    ? {
        title: 'Sentinel-5P / TROPOMI',
        subtitle: 'Спутниковое наблюдение атмосферы',
        layer: 'Слой TROPOMI',
        product: 'Продукт',
        coverage: 'Покрытие',
        date: 'Дата данных',
        opacity: 'Прозрачность',
        click: 'Кликните по ячейке для точного значения',
        selected: 'Выбранная ячейка',
        loading: 'Загрузка спутникового поля…',
        ready: 'Спутниковое поле загружено',
        off: 'Слой выключен',
        noData: 'Нет валидного спутникового покрытия',
        error: 'TROPOMI недоступен',
        disclaimer:
          'Столбовое спутниковое измерение. Не наземная концентрация и не прогноз CAMS. Цветовая шкала относительная P5–P95.',
        min: 'MIN',
        median: 'P50',
        max: 'MAX',
      }
    : {
        title: 'Sentinel-5P / TROPOMI',
        subtitle: 'Satellite atmospheric observation',
        layer: 'TROPOMI layer',
        product: 'Product',
        coverage: 'Coverage',
        date: 'Data date',
        opacity: 'Opacity',
        click: 'Click a cell for the exact value',
        selected: 'Selected cell',
        loading: 'Loading satellite field…',
        ready: 'Satellite field loaded',
        off: 'Layer off',
        noData: 'No valid satellite coverage',
        error: 'TROPOMI unavailable',
        disclaimer:
          'Satellite column retrieval. Not a ground concentration and not a CAMS forecast. Relative P5–P95 color scale.',
        min: 'MIN',
        median: 'P50',
        max: 'MAX',
      };
}

function createPanel(host) {
  host.innerHTML = `
    <div class="tropomi-card">
      <div class="tropomi-card__head">
        <div>
          <div class="tropomi-card__title" data-tropomi-copy="title"></div>
          <div class="tropomi-card__subtitle" data-tropomi-copy="subtitle"></div>
        </div>
        <label class="tropomi-toggle">
          <span data-tropomi-copy="layer"></span>
          <input id="tropomi-layer-toggle" type="checkbox" />
        </label>
      </div>

      <label class="tropomi-field">
        <span data-tropomi-copy="product"></span>
        <select id="tropomi-product">
          ${Object.entries(PRODUCT_LABELS)
            .map(([value, label]) => `<option value="${value}">${label}</option>`)
            .join('')}
        </select>
      </label>

      <div class="tropomi-metrics">
        <div><span data-tropomi-copy="min"></span><strong id="tropomi-min">—</strong></div>
        <div><span data-tropomi-copy="median"></span><strong id="tropomi-p50">—</strong></div>
        <div><span data-tropomi-copy="max"></span><strong id="tropomi-max">—</strong></div>
      </div>

      <div class="tropomi-legend">
        <div class="tropomi-legend__bar"></div>
        <div class="tropomi-legend__labels">
          <span id="tropomi-legend-min">—</span>
          <span id="tropomi-legend-mid">—</span>
          <span id="tropomi-legend-max">—</span>
        </div>
      </div>

      <div class="tropomi-meta">
        <div><span data-tropomi-copy="date"></span><strong id="tropomi-date">—</strong></div>
        <div><span data-tropomi-copy="coverage"></span><strong id="tropomi-coverage">—</strong></div>
      </div>

      <label class="tropomi-opacity">
        <span data-tropomi-copy="opacity"></span>
        <input id="tropomi-opacity" type="range" min="20" max="90" step="5" />
        <strong id="tropomi-opacity-value">—</strong>
      </label>

      <div class="tropomi-selected">
        <span data-tropomi-copy="selected"></span>
        <strong id="tropomi-selected-value">—</strong>
      </div>

      <div class="tropomi-hint" data-tropomi-copy="click"></div>
      <div class="tropomi-status" id="tropomi-status"></div>
      <div class="tropomi-disclaimer" data-tropomi-copy="disclaimer"></div>
    </div>
  `;
}

function applyCopy(host) {
  const strings = copy();
  host.querySelectorAll('[data-tropomi-copy]').forEach((element) => {
    const key = element.dataset.tropomiCopy;
    if (strings[key] != null) element.textContent = strings[key];
  });
}

function storedOpacity() {
  const raw = localStorage.getItem(OPACITY_KEY);
  if (raw == null || raw === '') return 55;
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) return 55;
  return Math.max(20, Math.min(90, parsed));
}

function fillExpression(stops) {
  const expression = ['interpolate', ['linear'], ['get', 'value']];
  stops.forEach((stop, index) => {
    expression.push(stop, COLORS[index]);
  });
  return expression;
}

function updateMetrics(host, field) {
  const stats = field.statistics || {};
  const product = field.product;
  const units = field.units;
  const meta = productDisplayMeta(product, units);

  const min = displayNumber(stats.min, product, units);
  const p50 = displayNumber(stats.p50, product, units);
  const max = displayNumber(stats.max, product, units);

  host.querySelector('#tropomi-min').textContent = `${min} ${meta.unit}`.trim();
  host.querySelector('#tropomi-p50').textContent = `${p50} ${meta.unit}`.trim();
  host.querySelector('#tropomi-max').textContent = `${max} ${meta.unit}`.trim();

  host.querySelector('#tropomi-legend-min').textContent = min;
  host.querySelector('#tropomi-legend-mid').textContent = p50;
  host.querySelector('#tropomi-legend-max').textContent = max;

  host.querySelector('#tropomi-date').textContent =
    field.selection?.resolved_date || field.time_from?.slice(0, 10) || '—';

  const coverage = finiteNumber(field.coverage?.valid_percent);
  host.querySelector('#tropomi-coverage').textContent =
    coverage == null ? '—' : `${coverage.toFixed(1)}%`;
}

function setStatus(host, key) {
  const strings = copy();
  host.querySelector('#tropomi-status').textContent = strings[key] || '';
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
          'fill-outline-color': 'rgba(255,255,255,0.06)',
        },
      },
      beforeId,
    );
  } else {
    map.setPaintProperty(LAYER_ID, 'fill-color', fillExpression(stops));
    map.setPaintProperty(LAYER_ID, 'fill-opacity', opacity / 100);
  }
}

export function installTropomiSatelliteLayer(map) {
  const host = document.getElementById('tropomi-air-root');
  if (!host || !map) return null;

  createPanel(host);
  applyCopy(host);

  const toggle = host.querySelector('#tropomi-layer-toggle');
  const product = host.querySelector('#tropomi-product');
  const opacity = host.querySelector('#tropomi-opacity');
  const opacityValue = host.querySelector('#tropomi-opacity-value');
  const selectedValue = host.querySelector('#tropomi-selected-value');

  let activeField = null;
  let requestSerial = 0;

  const initialOpacity = storedOpacity();
  opacity.value = String(initialOpacity);
  opacityValue.textContent = `${initialOpacity}%`;

  async function refresh() {
    const serial = ++requestSerial;
    setStatus(host, 'loading');

    const params = new URLSearchParams({
      product: product.value,
      timeliness: 'NRTI',
      stride: String(TROPOMI_RUNTIME_CONFIG.defaultStride),
      lookback_days: String(TROPOMI_RUNTIME_CONFIG.lookbackDays),
    });

    try {
      const response = await fetch(
        `${TROPOMI_RUNTIME_CONFIG.endpoint}?${params.toString()}`,
      );
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const field = await response.json();
      if (serial !== requestSerial) return;

      const collection = buildTropomiCellCollection(field);
      if (!collection.features.length) {
        setStatus(host, 'noData');
        return;
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
      updateMetrics(host, field);
      setStatus(host, 'ready');
    } catch (error) {
      console.error('TROPOMI field error:', error);
      setStatus(host, 'error');
    }
  }

  toggle.addEventListener('change', () => {
    if (!toggle.checked) {
      if (map.getLayer(LAYER_ID)) {
        map.setLayoutProperty(LAYER_ID, 'visibility', 'none');
      }
      setStatus(host, 'off');
      return;
    }
    refresh();
  });

  product.addEventListener('change', () => {
    if (toggle.checked) refresh();
  });

  opacity.addEventListener('input', () => {
    const value = Number(opacity.value);
    opacityValue.textContent = `${value}%`;
    localStorage.setItem(OPACITY_KEY, String(value));
    if (map.getLayer(LAYER_ID)) {
      map.setPaintProperty(LAYER_ID, 'fill-opacity', value / 100);
    }
  });

  map.on('click', LAYER_ID, (event) => {
    const feature = event.features?.[0];
    if (!feature || !activeField) return;
    selectedValue.textContent = formatSatelliteValue(
      feature.properties?.value,
      activeField.product,
      activeField.units,
    );
  });

  map.on('mouseenter', LAYER_ID, () => {
    map.getCanvas().style.cursor = 'crosshair';
  });

  map.on('mouseleave', LAYER_ID, () => {
    map.getCanvas().style.cursor = '';
  });

  const languageObserver = new MutationObserver(() => {
    applyCopy(host);
    if (!toggle.checked) {
      setStatus(host, 'off');
    } else if (activeField) {
      setStatus(host, 'ready');
    }
  });
  languageObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['lang'],
  });

  setStatus(host, 'off');

  return {
    refresh,
    destroy() {
      languageObserver.disconnect();
    },
  };
}
