import {
  renderVerticalTimeline,
} from "./evidenceTimelineUX.js";

export function appendEvidenceTimeline(
  baseHtml = "",
  evidencePayload = {},
) {
  const timeline = evidencePayload.timeline || [];

  return `
    ${baseHtml}
    ${renderVerticalTimeline(timeline)}
  `;
}
