const SUPPORTED_HORIZONS = [6, 12, 24, 48, 72];

export const DEFAULT_DRIFT_HORIZON = 24;
export const DEFAULT_DRIFT_PARTICLES = 300;
export const DEFAULT_DRIFT_RADIUS_M = 500;
export const DEFAULT_DRIFT_DIFFUSIVITY_M2_S = 2;

// WEATHER1_4_FORCING_MODE_UI
export const DRIFT_FORCING_CURRENT_ONLY = 'current_only';
export const DRIFT_FORCING_CURRENTS_PLUS_WIND =
  'currents_plus_wind';
export const DEFAULT_DRIFT_FORCING_MODE =
  DRIFT_FORCING_CURRENT_ONLY;
export const DEFAULT_DRIFT_WINDAGE_FACTOR = 0.02;


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


export function normalizeDriftHorizon(
  value,
  fallback = DEFAULT_DRIFT_HORIZON,
) {
  const number = finiteNumber(value);

  return SUPPORTED_HORIZONS.includes(number)
    ? number
    : fallback;
}


export function normalizeDriftParticles(
  value,
  fallback = DEFAULT_DRIFT_PARTICLES,
) {
  const number = finiteNumber(value);

  if (number === null) {
    return fallback;
  }

  const clamped = Math.min(
    1000,
    Math.max(100, number),
  );

  return Math.round(clamped / 100) * 100;
}


export function normalizeDriftForcingMode(
  value,
  fallback = DEFAULT_DRIFT_FORCING_MODE,
) {
  const normalized = String(value ?? '')
    .trim()
    .toLowerCase();

  if (
    normalized === DRIFT_FORCING_CURRENT_ONLY
    || normalized === DRIFT_FORCING_CURRENTS_PLUS_WIND
  ) {
    return normalized;
  }

  return fallback;
}


export function driftForcingViewModel(
  payload,
  requestedMode = DEFAULT_DRIFT_FORCING_MODE,
) {
  const requested = normalizeDriftForcingMode(
    requestedMode,
  );
  const mode = normalizeDriftForcingMode(
    payload?.forcing_mode,
    requested,
  );
  const windEnabled =
    mode === DRIFT_FORCING_CURRENTS_PLUS_WIND;
  const wind = windEnabled
    ? payload?.forcing?.wind
    : null;

  const payloadWindFactor = finiteNumber(
    payload?.simulation?.wind_drift_factor,
  );

  const sources = Array.isArray(wind?.sources)
    ? wind.sources
      .map((value) => String(value).trim())
      .filter(Boolean)
    : [];

  return {
    mode,
    windEnabled,
    windDriftFactor: windEnabled
      ? (
        payloadWindFactor
        ?? DEFAULT_DRIFT_WINDAGE_FACTOR
      )
      : 0,
    provider: wind?.provider ?? null,
    model: wind?.model ?? null,
    forecastReferenceTime:
      wind?.forecast_reference_time ?? null,
    sources,
    fallbackUsed: Boolean(wind?.fallback_used),
  };
}


export function driftApiUrl({
  longitude,
  latitude,
  hours = DEFAULT_DRIFT_HORIZON,
  particles = DEFAULT_DRIFT_PARTICLES,
  radiusM = DEFAULT_DRIFT_RADIUS_M,
  diffusivityM2S = DEFAULT_DRIFT_DIFFUSIVITY_M2_S,
  forcingMode = DEFAULT_DRIFT_FORCING_MODE,
}) {
  const params = new URLSearchParams({
    lon: String(Number(longitude)),
    lat: String(Number(latitude)),
    forcing_mode: normalizeDriftForcingMode(
      forcingMode,
    ),
    hours: String(
      normalizeDriftHorizon(hours),
    ),
    particles: String(
      normalizeDriftParticles(particles),
    ),
    radius_m: String(Number(radiusM)),
    diffusivity_m2_s: String(
      Number(diffusivityM2S),
    ),
  });

  return `/ocean/drift/?${params.toString()}`;
}


export async function fetchDriftForecast(
  options,
  fetchImpl = fetch,
) {
  const response = await fetchImpl(
    driftApiUrl(options),
  );

  if (!response.ok) {
    let detail = '';

    try {
      const payload = await response.json();
      detail = payload?.detail ?? '';
    } catch {
      detail = '';
    }

    throw new Error(
      detail
      || `Drift API HTTP ${response.status}`,
    );
  }

  return response.json();
}


export function snapshotForHorizon(
  payload,
  horizon,
) {
  const wanted = normalizeDriftHorizon(
    horizon,
  );

  return (
    payload?.horizons ?? []
  ).find(
    (item) => Number(item?.hours) === wanted,
  ) ?? null;
}


export function pointFeature(
  longitude,
  latitude,
  properties = {},
) {
  const lon = finiteNumber(longitude);
  const lat = finiteNumber(latitude);

  if (lon === null || lat === null) {
    return null;
  }

  return {
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: [lon, lat],
    },
    properties,
  };
}


export function emptyFeatureCollection() {
  return {
    type: 'FeatureCollection',
    features: [],
  };
}


export function driftSeedGeoJSON(seed) {
  const feature = pointFeature(
    seed?.longitude,
    seed?.latitude,
    { kind: 'seed' },
  );

  return {
    type: 'FeatureCollection',
    features: feature ? [feature] : [],
  };
}


export function driftCenterGeoJSON(snapshot) {
  const feature = pointFeature(
    snapshot?.center?.longitude,
    snapshot?.center?.latitude,
    {
      kind: 'center',
      hours: Number(snapshot?.hours ?? 0),
      particle_count: Number(
        snapshot?.particle_count ?? 0,
      ),
    },
  );

  return {
    type: 'FeatureCollection',
    features: feature ? [feature] : [],
  };
}


export function driftPointsGeoJSON(snapshot) {
  const features = (
    snapshot?.points ?? []
  )
    .map((point, index) => pointFeature(
      point?.[0],
      point?.[1],
      {
        kind: 'particle',
        index,
        hours: Number(snapshot?.hours ?? 0),
      },
    ))
    .filter(Boolean);

  return {
    type: 'FeatureCollection',
    features,
  };
}


export function driftEnvelopeGeoJSON(snapshot) {
  const geometry = snapshot?.envelope;

  if (
    !geometry
    || geometry.type !== 'Polygon'
    || !Array.isArray(geometry.coordinates)
  ) {
    return emptyFeatureCollection();
  }

  return {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry,
        properties: {
          kind: 'envelope',
          hours: Number(snapshot?.hours ?? 0),
        },
      },
    ],
  };
}


export function driftTrackGeoJSON(
  payload,
  horizon = null,
) {
  const normalizedHorizon = (
    horizon === null
      ? null
      : normalizeDriftHorizon(horizon)
  );

  const trackPoints = (
    payload?.mean_track ?? []
  );

  const limitedTrack = normalizedHorizon === null
    ? trackPoints
    : trackPoints.slice(
      0,
      normalizedHorizon + 1,
    );

  const coordinates = limitedTrack
    .map((point) => [
      finiteNumber(point?.longitude),
      finiteNumber(point?.latitude),
    ])
    .filter(
      ([longitude, latitude]) => (
        longitude !== null
        && latitude !== null
      ),
    );

  if (coordinates.length < 2) {
    return emptyFeatureCollection();
  }

  return {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        geometry: {
          type: 'LineString',
          coordinates,
        },
        properties: {
          kind: 'mean_track',
        },
      },
    ],
  };
}
