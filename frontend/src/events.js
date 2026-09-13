export const CATEGORY_META = Object.freeze({
  industrial_fire: { label: 'Industrial fire', color: '#ff5d5d' },
  wildfire: { label: 'Wildfire', color: '#ff9f43' },
  oil_spill: { label: 'Oil spill', color: '#6f8cff' },
  water_pollution: { label: 'Water pollution', color: '#46d7c8' },
  algae_bloom: { label: 'Algae bloom', color: '#8bd96b' },
  marine_animal_death: { label: 'Marine animal death', color: '#bd7cff' },
  chemical_release: { label: 'Chemical release', color: '#f2d95c' },
  storm_damage: { label: 'Storm damage', color: '#84b6ff' },
});

export const DEFAULT_CATEGORY_META = Object.freeze({
  label: 'Environmental incident',
  color: '#d3dce8',
});

export function categoryMeta(category) {
  return CATEGORY_META[category] ?? DEFAULT_CATEGORY_META;
}

export function normalizeMonitorEvent(raw) {
  if (!raw || typeof raw !== 'object') return null;

  const id = String(raw.id ?? '').trim();
  const category = String(raw.category ?? '').trim();
  const status = String(raw.status ?? 'detected').trim();
  const location = raw.location && typeof raw.location === 'object'
    ? raw.location
    : {};

  const rawLatitude = location.latitude;
  const rawLongitude = location.longitude;

  const latitude = rawLatitude === null || rawLatitude === ''
    ? Number.NaN
    : Number(rawLatitude);

  const longitude = rawLongitude === null || rawLongitude === ''
    ? Number.NaN
    : Number(rawLongitude);

  if (
    !id
    || !Number.isFinite(latitude)
    || !Number.isFinite(longitude)
    || latitude < -90
    || latitude > 90
    || longitude < -180
    || longitude > 180
  ) return null;

  const meta = categoryMeta(category);

  return {
    id,
    category,
    categoryLabel: meta.label,
    markerColor: meta.color,
    status,
    locationName: String(location.name ?? 'Unknown location').trim()
      || 'Unknown location',
    latitude,
    longitude,
    confidence: Number.isFinite(Number(raw.confidence))
      ? Number(raw.confidence)
      : null,
    severity: String(raw.severity ?? 'unknown').trim() || 'unknown',
    evidenceCount: Number.isFinite(Number(raw.evidence_count))
      ? Number(raw.evidence_count)
      : 0,
    primaryTitle: String(raw.primary_title ?? '').trim(),
    firstSeen: raw.first_seen ?? null,
    lastSeen: raw.last_seen ?? null,
    updatedAt: raw.updated_at ?? null,
  };
}

export function normalizeMonitorEvents(rows) {
  if (!Array.isArray(rows)) return [];
  return rows.map(normalizeMonitorEvent).filter(Boolean);
}

export function eventsToFeatureCollection(events) {
  return {
    type: 'FeatureCollection',
    features: events.map((event) => ({
      type: 'Feature',
      id: event.id,
      geometry: {
        type: 'Point',
        coordinates: [event.longitude, event.latitude],
      },
      properties: { ...event },
    })),
  };
}

export async function fetchMonitorEvents(fetchImpl = fetch) {
  const response = await fetchImpl('/monitor/events/', {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Monitor API returned HTTP ${response.status}`);
  }

  return normalizeMonitorEvents(await response.json());
}

export async function fetchEventEvidence(eventId, fetchImpl = fetch) {
  const response = await fetchImpl(
    `/monitor/events/${encodeURIComponent(eventId)}/evidence`,
    { headers: { Accept: 'application/json' } },
  );

  if (!response.ok) {
    throw new Error(`Evidence API returned HTTP ${response.status}`);
  }

  const rows = await response.json();
  return Array.isArray(rows) ? rows : [];
}
