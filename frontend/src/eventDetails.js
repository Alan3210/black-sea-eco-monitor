export function humanizeToken(value) {
  const text = String(value ?? '').trim();

  if (!text) return 'Unknown';

  return text
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function formatConfidence(value) {
  const number = Number(value);

  if (!Number.isFinite(number)) return '—';

  return `${Math.round(number * 100)}%`;
}

export function formatEventDate(value) {
  if (!value) return '—';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString();
}

export function safeExternalHttpUrl(value) {
  try {
    const url = new URL(String(value ?? ''));

    if (!['http:', 'https:'].includes(url.protocol)) {
      return null;
    }

    return url.href;
  } catch {
    return null;
  }
}

export function locationScopeLabel(value) {
  const normalized = String(value ?? '').trim().toLowerCase();

  const labels = {
    city: 'City-level',
    settlement: 'Settlement-level',
    district: 'District-level',
    street: 'Street-level',
    facility: 'Facility-level',
    protected_area: 'Protected-area',
    coastal_area: 'Coastal-area',
    water_body: 'Water-body',
    region: 'Region-level',
    other: 'Approximate',
  };

  return labels[normalized] ?? 'Unknown';
}

export function coordinateInterpretation(event) {
  if (event?.coordinateSource === 'canonical_database') {
    return 'Representative map point — not exact incident coordinates.';
  }

  if (event?.coordinateSource) {
    return 'Coordinates include source provenance; verify precision before field use.';
  }

  return 'Coordinate provenance is unavailable.';
}

export function eventDetailsViewModel(event) {
  return {
    id: event?.id ?? '',
    category: event?.categoryLabel || humanizeToken(event?.category),
    color: event?.markerColor || '#d3dce8',
    location: event?.locationName || 'Unknown location',
    headline: event?.primaryTitle || 'Environmental incident',
    status: humanizeToken(event?.status),
    severity: humanizeToken(event?.severity),
    confidence: formatConfidence(event?.confidence),
    locationConfidence: formatConfidence(event?.locationConfidence),
    locationType: humanizeToken(event?.locationType),
    locationScope: locationScopeLabel(event?.locationType),
    coordinateSource: humanizeToken(event?.coordinateSource),
    coordinateInterpretation: coordinateInterpretation(event),
    evidenceCount: Number.isFinite(Number(event?.evidenceCount))
      ? Number(event.evidenceCount)
      : 0,
    coordinates: Number.isFinite(event?.latitude) && Number.isFinite(event?.longitude)
      ? `${event.latitude.toFixed(4)}, ${event.longitude.toFixed(4)}`
      : '—',
    incidentTime: formatEventDate(event?.incidentTime),
    detectionTime: formatEventDate(event?.detectionTime),
    sourceTime: formatEventDate(event?.sourceTime),
    firstSeen: formatEventDate(event?.firstSeen),
    lastSeen: formatEventDate(event?.lastSeen || event?.updatedAt),
  };
}
