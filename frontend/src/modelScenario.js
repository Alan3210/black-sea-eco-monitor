const MARINE_EVENT_CATEGORIES = new Set([
  'oil_spill',
  'water_pollution',
  'algae_bloom',
  'marine_animal_death',
]);

const MARINE_LOCATION_TYPES = new Set([
  'water_body',
  'coastal_area',
]);


export function eventCanSeedMarineModel(event) {
  const category = String(
    event?.category ?? '',
  ).trim().toLowerCase();

  const locationType = String(
    event?.locationType ?? '',
  ).trim().toLowerCase();

  return (
    MARINE_EVENT_CATEGORIES.has(category)
    && MARINE_LOCATION_TYPES.has(locationType)
    && Number.isFinite(Number(event?.latitude))
    && Number.isFinite(Number(event?.longitude))
  );
}


function coordinatePairs(value, result = []) {
  if (!Array.isArray(value)) {
    return result;
  }

  if (
    value.length >= 2
    && Number.isFinite(Number(value[0]))
    && Number.isFinite(Number(value[1]))
  ) {
    result.push([
      Number(value[0]),
      Number(value[1]),
    ]);
    return result;
  }

  for (const child of value) {
    coordinatePairs(child, result);
  }

  return result;
}


export function satelliteCandidateSeed(feature) {
  const pairs = coordinatePairs(
    feature?.geometry?.coordinates,
  );

  if (!pairs.length) {
    return null;
  }

  const sums = pairs.reduce(
    (acc, [longitude, latitude]) => {
      acc.longitude += longitude;
      acc.latitude += latitude;
      return acc;
    },
    {
      longitude: 0,
      latitude: 0,
    },
  );

  const sourceId = String(
    feature?.properties?.candidate_id
    ?? feature?.properties?.observation_id
    ?? feature?.id
    ?? 'sar_candidate',
  );

  return {
    longitude: sums.longitude / pairs.length,
    latitude: sums.latitude / pairs.length,
    sourceKind: 'sar_candidate',
    sourceId,
  };
}


export function seedStatusKey(
  sourceKind,
  {
    forecastReady = false,
  } = {},
) {
  const suffix = (
    sourceKind === 'event'
      ? 'Event'
      : sourceKind === 'sar_candidate'
        ? 'Sar'
        : sourceKind === 'manual'
          ? 'Manual'
          : 'Unknown'
  );

  return forecastReady
    ? `workflow.forecastReady${suffix}`
    : `workflow.prepared${suffix}`;
}

export function modelScenarioShouldPersist(
  {
    seedAvailable = false,
    forecastAvailable = false,
    driftLoading = false,
    impactAvailable = false,
    impactLoading = false,
    impactError = false,
  } = {},
) {
  return Boolean(
    seedAvailable
    || forecastAvailable
    || driftLoading
    || impactAvailable
    || impactLoading
    || impactError
  );
}

