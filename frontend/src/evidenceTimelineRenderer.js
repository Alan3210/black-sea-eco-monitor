import {
  buildVisualTimeline,
} from "./evidenceTimelineVisual.js";

export function renderEvidenceTimeline(events = []) {
  const timeline = buildVisualTimeline(events);

  return `
    <section class="evidence-panel-card evidence-timeline-card">
      <h3>Evidence Timeline</h3>

      <div class="evidence-timeline">
        ${timeline.map((event) => `
          <div class="timeline-event ${event.className}">
            <div class="timeline-icon">
              ${event.icon}
            </div>

            <div class="timeline-content">
              <strong>${event.title}</strong>
              <span>${event.time || ""}</span>
              ${
                event.source
                ? `<small>${event.source}</small>`
                : ""
              }
            </div>
          </div>
        `).join("")}
      </div>
    </section>
  `;
}
