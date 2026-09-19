export const DEFAULT_IMPACT_THRESHOLD_KM = 5.0;

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


export async function fetchDriftImpact(
  forecast,
  {
    thresholdKm = DEFAULT_IMPACT_THRESHOLD_KM,
  } = {},
  fetchImpl = fetch,
) {
  const response = await fetchImpl(
    '/impact/drift',
    {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        forecast,
        proximity_threshold_km: Number(thresholdKm),
      }),
    },
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
      || `Impact API HTTP ${response.status}`,
    );
  }

  return response.json();
}


export function impactAssessmentsToFeatureCollection(payload) {
  const features = (
    payload?.assessments ?? []
  )
    .map((assessment) => {
      const target = assessment?.target ?? {};
      const position = target?.position ?? {};

      const latitude = finiteNumber(position.latitude);
      const longitude = finiteNumber(position.longitude);

      if (
        latitude === null
        || longitude === null
        || latitude < -90
        || latitude > 90
        || longitude < -180
        || longitude > 180
      ) {
        return null;
      }

      return {
        type: 'Feature',
        id: target.id ?? undefined,
        geometry: {
          type: 'Point',
          coordinates: [
            longitude,
            latitude,
          ],
        },
        properties: {
          id: String(target.id ?? ''),
          name: String(target.name ?? ''),
          type: target.type ?? null,
          withinThreshold: Boolean(
            assessment?.potentially_affected,
          ),
          firstExposureHours: finiteNumber(
            assessment?.first_exposure_hours,
          ),
          minimumDistanceKm: finiteNumber(
            assessment?.minimum_distance_km,
          ),
          closestHorizonHours: finiteNumber(
            assessment?.closest_horizon_hours,
          ),
        },
      };
    })
    .filter(Boolean);

  return {
    type: 'FeatureCollection',
    features,
  };
}


export function impactSummaryViewModel(payload) {
  return {
    targetCount: Number.isFinite(
      Number(payload?.target_count),
    )
      ? Number(payload.target_count)
      : 0,
    withinThresholdCount: Number.isFinite(
      Number(payload?.potentially_affected_count),
    )
      ? Number(payload.potentially_affected_count)
      : 0,
    thresholdKm: Number.isFinite(
      Number(payload?.proximity_threshold_km),
    )
      ? Number(payload.proximity_threshold_km)
      : DEFAULT_IMPACT_THRESHOLD_KM,
    analysisType: String(
      payload?.analysis_type
      ?? 'drift_proximity_screening_v0.1',
    ),
    targetSource: String(
      payload?.target_source
      ?? 'event_store_known_locations',
    ),
    assessments: Array.isArray(payload?.assessments)
      ? payload.assessments
      : [],
  };
}
