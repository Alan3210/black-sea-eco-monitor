import {
  normalizeEventTimeline,
} from "./realEvidenceTimelineBinding.js";

import {
  renderVerticalTimeline,
} from "./evidenceTimelineUX.js";

export function renderRealEventTimeline(event = {}) {
  const timeline = normalizeEventTimeline(event);

  if (!timeline.length) {
    return `
      <div class="evidence-timeline-empty">
        No timeline events available
      </div>
    `;
  }

  return renderVerticalTimeline(timeline);
}
