function normalizeLocation(location) {
  if (!location) {
    return null;
  }

  const latitude = Number(location.latitude);
  const longitude = Number(location.longitude);

  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude)
  ) {
    return null;
  }

  return {
    latitude,
    longitude,
  };
}


function normalizeConfidence(value) {
  if (
    value === null ||
    value === undefined ||
    value === ''
  ) {
    return null;
  }

  const confidence = Number(value);

  if (!Number.isFinite(confidence)) {
    return null;
  }

  return Math.min(
    1,
    Math.max(0, confidence),
  );
}


export function normalizeInvestigationEvidence(
  record = {},
) {
  return {
    id: record.id ?? null,

    eventId:
      record.event_id ??
      record.eventId ??
      null,

    type:
      record.evidence_type ??
      record.type ??
      'unknown',

    source: record.source ?? null,

    timestamp: record.timestamp ?? null,

    confidence: normalizeConfidence(
      record.confidence,
    ),

    title: record.title ?? null,

    location: normalizeLocation(
      record.location,
    ),

    metadata:
      record.metadata &&
      typeof record.metadata === 'object'
        ? record.metadata
        : {},

    provenance:
      record.provenance &&
      typeof record.provenance === 'object'
        ? record.provenance
        : {},
  };
}


export function normalizeInvestigationPayload(
  payload = {},
) {
  const evidence = Array.isArray(
    payload.evidence,
  )
    ? payload.evidence.map(
        normalizeInvestigationEvidence,
      )
    : [];

  const candidateSources = Array.isArray(
    payload.candidate_sources,
  )
    ? payload.candidate_sources
    : Array.isArray(payload.candidateSources)
      ? payload.candidateSources
      : [];

  return {
    eventId:
      payload.event_id ??
      payload.eventId ??
      null,

    evidence,

    candidateSources,
  };
}