export function normalizeSatelliteCandidateFeatureCollection(raw) {
  const features = Array.isArray(raw?.features)
    ? raw.features
    : [];

  return {
    type: 'FeatureCollection',
    features: features.filter((feature) => (
      feature
      && feature.type === 'Feature'
      && feature.geometry
      && feature.properties?.observation_type === 'sar_dark_spot_candidate'
      && feature.properties?.derivation_level === 'derived'
    )),
    semantics: raw?.semantics ?? null,
  };
}

export async function fetchSatelliteCandidates(fetchImpl = fetch) {
  const response = await fetchImpl(
    '/satellite/observations/candidates.geojson',
    {
      headers: { Accept: 'application/geo+json, application/json' },
    },
  );

  if (!response.ok) {
    throw new Error(
      `Satellite API returned HTTP ${response.status}`,
    );
  }

  return normalizeSatelliteCandidateFeatureCollection(
    await response.json(),
  );
}

export function satelliteCandidateViewModel(feature) {
  const properties = feature?.properties ?? {};

  return {
    id: String(
      properties.candidate_id
      ?? properties.observation_id
      ?? feature?.id
      ?? 'candidate',
    ),
    areaKm2: Number.isFinite(Number(properties.area_km2))
      ? Number(properties.area_km2)
      : null,
    meanVvDb: Number.isFinite(Number(properties.mean_vv_db))
      ? Number(properties.mean_vv_db)
      : null,
    thresholdDb: Number.isFinite(Number(properties.threshold_db))
      ? Number(properties.threshold_db)
      : null,
    acquisitionTime: properties.acquisition_time ?? null,
    reviewStatus: String(
      properties.review_status ?? 'unreviewed',
    ),
    confidence: properties.confidence ?? null,
  };
}
