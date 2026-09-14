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
    evidenceCount: Number.isFinite(Number(event?.evidenceCount))
      ? Number(event.evidenceCount)
      : 0,
    coordinates: Number.isFinite(event?.latitude) && Number.isFinite(event?.longitude)
      ? `${event.latitude.toFixed(4)}, ${event.longitude.toFixed(4)}`
      : '—',
    firstSeen: formatEventDate(event?.firstSeen),
    lastSeen: formatEventDate(event?.lastSeen || event?.updatedAt),
  };
}
