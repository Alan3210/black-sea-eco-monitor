import {
  buildEvidenceEventTimeline,
} from "./evidenceEventTimeline.js";

import {
  renderEvidenceTimeline,
} from "./evidenceTimelineRenderer.js";

export function createTimelineFromEvent(
  event = {},
) {
  return buildEvidenceEventTimeline(
    event.timeline || [],
  );
}

export function renderEventTimelineForPanel(
  event = {},
) {
  return renderEvidenceTimeline(
    event.timeline || [],
  );
}

export function updateTimelineFromSelectedEvent(
  eventId,
  eventPayload = {},
) {
  if (!eventId) {
    return null;
  }

  return {
    eventId,
    timeline: createTimelineFromEvent(eventPayload),
  };
}
