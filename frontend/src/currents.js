const DEFAULT_STRIDE = 12;

const MIN_ARROW_SIZE_PERCENT = 60;
const MAX_ARROW_SIZE_PERCENT = 200;
const DEFAULT_ARROW_SIZE_PERCENT = 100;


export function normalizeCurrentArrowSizePercent(
  value,
  fallback = DEFAULT_ARROW_SIZE_PERCENT,
) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return fallback;
  }

  return Math.min(
    MAX_ARROW_SIZE_PERCENT,
    Math.max(
      MIN_ARROW_SIZE_PERCENT,
      Math.round(number / 10) * 10,
    ),
  );
}


export function currentArrowSizeExpression(
  percent = DEFAULT_ARROW_SIZE_PERCENT,
) {
  const normalized = normalizeCurrentArrowSizePercent(
    percent,
  );
  const scale = normalized / 100;

  return [
    'interpolate',
    ['linear'],
    ['get', 'speed'],
    0, 0.72 * scale,
    0.08, 0.82 * scale,
    0.15, 0.95 * scale,
    0.35, 1.10 * scale,
    0.7, 1.28 * scale,
  ];
}


function finiteNumber(value) {
  if (
    value === null
    || value === undefined
    || value === ''
  ) {
    return null;
  }

  const number = Number(value);
  return Number.isFinite(number)
    ? number
    : null;
}

export function buildCurrentsUrl({
  at = null,
  stride = DEFAULT_STRIDE,
} = {}) {
  const params = new URLSearchParams();
  params.set('stride', String(stride));

  if (at) {
    params.set('at', String(at));
  }

  return `/ocean/currents/?${params.toString()}`;
}

export function normalizeCurrentsPayload(payload) {
  const sourceVectors = Array.isArray(payload?.vectors)
    ? payload.vectors
    : [];

  const vectors = sourceVectors
    .map((row) => {
      const longitude = finiteNumber(row?.longitude);
      const latitude = finiteNumber(row?.latitude);
      const u = finiteNumber(row?.u);
      const v = finiteNumber(row?.v);
      const speed = finiteNumber(row?.speed);
      const directionDeg = finiteNumber(row?.direction_deg);

      if (
        longitude === null
        || latitude === null
        || u === null
        || v === null
        || speed === null
        || directionDeg === null
      ) {
        return null;
      }

      return {
        longitude,
        latitude,
        u,
        v,
        speed,
        direction_deg: Number(
          (
            (
              (directionDeg % 360)
              + 360
            ) % 360
          ).toFixed(6)
        ),
      };
    })
    .filter(Boolean);

  return {
    dataset_id: String(payload?.dataset_id ?? ''),
    source: String(payload?.source ?? ''),
    product: String(payload?.product ?? ''),
    valid_time: payload?.valid_time
      ? String(payload.valid_time)
      : null,
    requested_time: payload?.requested_time
      ? String(payload.requested_time)
      : null,
    depth_m: finiteNumber(payload?.depth_m),
    variable_units: String(payload?.variable_units ?? 'm/s'),
    precision: String(payload?.precision ?? ''),
    cache: payload?.cache ?? null,
    vector_count: vectors.length,
    vectors,
  };
}

export async function fetchOceanCurrents(options = {}) {
  const response = await fetch(
    buildCurrentsUrl(options),
    {
      headers: {
        Accept: 'application/json',
      },
    },
  );

  if (!response.ok) {
    const detail = await response
      .json()
      .then((value) => value?.detail)
      .catch(() => null);

    throw new Error(
      detail
      || `Ocean currents API returned ${response.status}`,
    );
  }

  return normalizeCurrentsPayload(
    await response.json(),
  );
}

export function currentsToFeatureCollection(payload) {
  const normalized = normalizeCurrentsPayload(payload);

  return {
    type: 'FeatureCollection',
    features: normalized.vectors.map((vector, index) => ({
      type: 'Feature',
      id: index,
      geometry: {
        type: 'Point',
        coordinates: [
          vector.longitude,
          vector.latitude,
        ],
      },
      properties: {
        u: vector.u,
        v: vector.v,
        speed: vector.speed,
        direction_deg: vector.direction_deg,
      },
    })),
  };
}

const DIRECTIONS = {
  ru: ['С', 'СВ', 'В', 'ЮВ', 'Ю', 'ЮЗ', 'З', 'СЗ'],
  en: ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
};

export function cardinalDirection(
  degrees,
  language = 'ru',
) {
  const value = finiteNumber(degrees);

  if (value === null) return '—';

  const normalized = ((value % 360) + 360) % 360;
  const index = Math.round(normalized / 45) % 8;
  const labels = DIRECTIONS[language] ?? DIRECTIONS.en;

  return labels[index];
}

export function formatCurrentSpeed(value) {
  const speed = finiteNumber(value);

  if (speed === null) return '—';

  return `${speed.toFixed(2)} m/s`;
}

export function formatCurrentValidTime(
  value,
  locale = 'ru-RU',
) {
  if (!value) return '—';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat(
    locale,
    {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
      timeZoneName: 'short',
    },
  ).format(date);
}
