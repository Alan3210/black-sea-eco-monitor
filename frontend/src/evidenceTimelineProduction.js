import {
  renderVerticalTimeline,
} from "./evidenceTimelineUX.js";

export function buildProductionTimelineBlock(
  evidencePayload = {},
) {
  return renderVerticalTimeline(
    evidencePayload.timeline || [],
  );
}

export function mountProductionTimeline(
  container,
  evidencePayload = {},
) {
  if (!container) {
    return false;
  }

  container.innerHTML = buildProductionTimelineBlock(
    evidencePayload,
  );

  return true;
}
