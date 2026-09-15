export const DEFAULT_STATUSES = Object.freeze([
  'detected',
  'active',
  'contained',
  'resolved',
]);

export const DEFAULT_CATEGORIES = Object.freeze([
  'wildfire',
  'industrial_fire',
  'oil_spill',
  'water_pollution',
  'algae_bloom',
  'marine_animal_death',
  'chemical_release',
  'storm_damage',
]);

export function eventReferenceTime(event) {
  const candidates = [
    event?.incidentTime,
    event?.sourceTime,
    event?.detectionTime,
    event?.lastSeen,
    event?.updatedAt,
    event?.firstSeen,
  ];

  for (const value of candidates) {
    if (!value) continue;
    const time = Date.parse(value);
    if (Number.isFinite(time)) return time;
  }

  return null;
}

export function filterEvents(
  events,
  {
    statuses = DEFAULT_STATUSES,
    categories = DEFAULT_CATEGORIES,
    days = 7,
    now = Date.now(),
  } = {},
) {
  const statusSet = new Set(statuses);
  const categorySet = new Set(categories);

  const cutoff = days === 'all'
    ? null
    : now - Number(days) * 86_400_000;

  return events.filter((event) => {
    if (!statusSet.has(event.status)) return false;
    if (!categorySet.has(event.category)) return false;

    if (cutoff === null) return true;

    const referenceTime = eventReferenceTime(event);

    // If the store has no usable time metadata, keep the event visible rather
    // than silently hiding it from the operator.
    if (referenceTime === null) return true;

    return referenceTime >= cutoff;
  });
}
