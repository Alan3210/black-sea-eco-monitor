const DEFAULT_WIND_STRIDE = 2;

const MIN_ARROW_SIZE_PERCENT = 60;
const MAX_ARROW_SIZE_PERCENT = 200;
const DEFAULT_ARROW_SIZE_PERCENT = 100;


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


function normalizedDegrees(value) {
  const number = finiteNumber(value);

  if (number === null) {
    return null;
  }

  return Number(
    (
      (
        (number % 360)
        + 360
      ) % 360
    ).toFixed(6),
  );
}


export function normalizeWindArrowSizePercent(
  value,
  fallback = DEFAULT_ARROW_SIZE_PERCENT,
) {
  const number = finiteNumber(value);

  if (number === null) {
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


export function windArrowSizeExpression(
  percent = DEFAULT_ARROW_SIZE_PERCENT,
) {
  const scale =
    normalizeWindArrowSizePercent(
      percent,
    ) / 100;

  return [
    'interpolate',
    ['linear'],
    ['get', 'speed'],
    0, 0.58 * scale,
    2, 0.72 * scale,
    5, 0.90 * scale,
    10, 1.12 * scale,
    15, 1.30 * scale,
  ];
}


export function buildWindFieldUrl({
  at = null,
  stride = DEFAULT_WIND_STRIDE,
} = {}) {
  const params = new URLSearchParams();

  const normalizedStride =
    Math.min(
      8,
      Math.max(
        1,
        Math.round(
          finiteNumber(stride)
          ?? DEFAULT_WIND_STRIDE,
        ),
      ),
    );

  params.set(
    'stride',
    String(normalizedStride),
  );

  if (at) {
    params.set(
      'at',
      String(at),
    );
  }

  return (
    `/weather/wind-field?`
    + params.toString()
  );
}


export function normalizeWindFieldPayload(
  payload,
) {
  const sourceVectors =
    Array.isArray(payload?.vectors)
      ? payload.vectors
      : [];

  const vectors = sourceVectors
    .map((row) => {
      const longitude = finiteNumber(
        row?.longitude,
      );
      const latitude = finiteNumber(
        row?.latitude,
      );
      // Accept both the raw WEATHER-1.5A API field names and
      // the already-normalized frontend aliases. This keeps
      // normalizeWindFieldPayload idempotent, which is important
      // because fetchWindField normalizes once and
      // windToFeatureCollection normalizes defensively again.
      const u = finiteNumber(
        row?.u_ms
        ?? row?.u,
      );
      const v = finiteNumber(
        row?.v_ms
        ?? row?.v,
      );
      const speed = finiteNumber(
        row?.speed_ms
        ?? row?.speed,
      );
      const directionFromDeg =
        normalizedDegrees(
          row?.direction_from_deg,
        );
      const directionToDeg =
        normalizedDegrees(
          row?.direction_to_deg,
        );

      if (
        longitude === null
        || latitude === null
        || u === null
        || v === null
        || speed === null
        || directionFromDeg === null
        || directionToDeg === null
      ) {
        return null;
      }

      return {
        longitude,
        latitude,
        u,
        v,
        speed,
        direction_from_deg:
          directionFromDeg,
        direction_to_deg:
          directionToDeg,
      };
    })
    .filter(Boolean);

  return {
    provider:
      String(
        payload?.provider
        ?? 'ecmwf',
      ),
    model:
      String(
        payload?.model
        ?? 'ifs',
      ),
    product:
      String(
        payload?.product
        ?? '',
      ),
    height_m:
      finiteNumber(
        payload?.height_m,
      ),
    requested_time:
      payload?.requested_time
        ? String(
          payload.requested_time,
        )
        : null,
    valid_time:
      payload?.valid_time
        ? String(
          payload.valid_time,
        )
        : null,
    forecast_reference_time:
      payload?.forecast_reference_time
        ? String(
          payload.forecast_reference_time,
        )
        : null,
    retrieved_at:
      payload?.retrieved_at
        ? String(
          payload.retrieved_at,
        )
        : null,
    sources:
      Array.isArray(payload?.sources)
        ? payload.sources.map(String)
        : [],
    fallback_used:
      Boolean(
        payload?.fallback_used,
      ),
    temporal_interpolation:
      String(
        payload?.temporal_interpolation
        ?? '',
      ),
    direction_convention:
      payload?.direction_convention
      ?? null,
    bbox:
      payload?.bbox
      ?? null,
    stride:
      finiteNumber(
        payload?.stride,
      ),
    native_grid_shape:
      payload?.native_grid_shape
      ?? null,
    speed_stats:
      payload?.speed_stats
      ?? null,
    vector_count:
      vectors.length,
    vectors,
  };
}


export async function fetchWindField(
  options = {},
  fetchImpl = fetch,
) {
  const response = await fetchImpl(
    buildWindFieldUrl(
      options,
    ),
    {
      headers: {
        Accept: 'application/json',
      },
    },
  );

  if (!response.ok) {
    const detail = await response
      .json()
      .then(
        (value) => value?.detail,
      )
      .catch(
        () => null,
      );

    throw new Error(
      detail
      || (
        'Wind field API returned '
        + response.status
      ),
    );
  }

  return normalizeWindFieldPayload(
    await response.json(),
  );
}


export function windToFeatureCollection(
  payload,
) {
  const normalized =
    normalizeWindFieldPayload(
      payload,
    );

  return {
    type: 'FeatureCollection',
    features:
      normalized.vectors.map(
        (vector, index) => ({
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
            direction_from_deg:
              vector.direction_from_deg,
            direction_to_deg:
              vector.direction_to_deg,
          },
        }),
      ),
  };
}


export function formatWindSpeed(
  value,
) {
  const speed = finiteNumber(
    value,
  );

  if (speed === null) {
    return '—';
  }

  return `${speed.toFixed(1)} m/s`;
}
