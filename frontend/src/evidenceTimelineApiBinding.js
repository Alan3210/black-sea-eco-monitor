import {
  buildEvidenceEventTimeline,
} from "./evidenceEventTimeline.js";

export function extractTimelineFromEvidencePayload(
  payload = {},
) {
  return payload.timeline || [];
}

export function buildTimelineFromEvidencePayload(
  payload = {},
) {
  return buildEvidenceEventTimeline(
    extractTimelineFromEvidencePayload(payload),
  );
}

export function createEvidenceTimelineRequest(
  eventId,
) {
  if (!eventId) {
    return null;
  }

  return {
    endpoint: "/air/evidence-crosscheck",
    params: {
      event_id: eventId,
      include_timeline: true,
    },
  };
}
