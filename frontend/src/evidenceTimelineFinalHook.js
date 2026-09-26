import {
  mountProductionTimeline,
} from "./evidenceTimelineProduction.js";

export function mountEvidenceTimelineToPanel(
  container,
  evidencePayload = {},
) {
  return mountProductionTimeline(
    container,
    evidencePayload,
  );
}
