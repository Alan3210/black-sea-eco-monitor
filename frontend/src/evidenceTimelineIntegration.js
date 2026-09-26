import {
  buildEvidenceEventTimeline,
  renderEvidenceEventTimeline,
} from "./evidenceEventTimeline.js";

export function buildEvidencePanelTimelineBlock(
  events = [],
) {
  return buildEvidenceEventTimeline(events);
}

export function renderEvidencePanelTimelineBlock(
  events = [],
) {
  return renderEvidenceEventTimeline(
    buildEvidencePanelTimelineBlock(events),
  );
}

export function composeEvidencePanelContent(
  baseContent = "",
  events = [],
) {
  return `
    ${baseContent}
    ${renderEvidencePanelTimelineBlock(events)}
  `;
}
