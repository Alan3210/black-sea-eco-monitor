import {
  categoryLabel,
  coordinateSourceLabel,
  localeForLanguage,
  localizeLocationName,
  locationScopeLabel as translatedLocationScopeLabel,
  locationTypeLabel,
  severityLabel,
  statusLabel,
  t,
} from './i18n.js';

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

export function formatEventDate(value, language = 'en') {
  if (!value) return '—';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString(
    localeForLanguage(language),
  );
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

export function locationScopeLabel(value, language = 'en') {
  return translatedLocationScopeLabel(
    value,
    language,
  );
}

export function coordinateInterpretation(
  event,
  language = 'en',
) {
  if (event?.coordinateSource === 'canonical_database') {
    return t(
      language,
      'coordinateNote.canonical',
    );
  }

  if (event?.coordinateSource) {
    return t(
      language,
      'coordinateNote.provenance',
    );
  }

  return t(
    language,
    'coordinateNote.unknown',
  );
}

export function eventDetailsViewModel(
  event,
  language = 'en',
) {
  return {
    id: event?.id ?? '',
    category: categoryLabel(
      event?.category,
      language,
    ),
    color: event?.markerColor || '#d3dce8',
    location: localizeLocationName(
      event?.locationName,
      language,
    ),
    headline: event?.primaryTitle
      || t(language, 'headline.fallback'),
    status: statusLabel(
      event?.status,
      language,
    ),
    severity: severityLabel(
      event?.severity,
      language,
    ),
    confidence: formatConfidence(event?.confidence),
    locationConfidence: formatConfidence(
      event?.locationConfidence,
    ),
    locationType: locationTypeLabel(
      event?.locationType,
      language,
    ),
    locationScope: translatedLocationScopeLabel(
      event?.locationType,
      language,
    ),
    coordinateSource: coordinateSourceLabel(
      event?.coordinateSource,
      language,
    ),
    coordinateInterpretation: coordinateInterpretation(
      event,
      language,
    ),
    evidenceCount: Number.isFinite(Number(event?.evidenceCount))
      ? Number(event.evidenceCount)
      : 0,
    coordinates: Number.isFinite(event?.latitude) && Number.isFinite(event?.longitude)
      ? `${event.latitude.toFixed(4)}, ${event.longitude.toFixed(4)}`
      : '—',
    incidentTime: formatEventDate(
      event?.incidentTime,
      language,
    ),
    detectionTime: formatEventDate(
      event?.detectionTime,
      language,
    ),
    sourceTime: formatEventDate(
      event?.sourceTime,
      language,
    ),
    firstSeen: formatEventDate(
      event?.firstSeen,
      language,
    ),
    lastSeen: formatEventDate(
      event?.lastSeen || event?.updatedAt,
      language,
    ),
  };
}
