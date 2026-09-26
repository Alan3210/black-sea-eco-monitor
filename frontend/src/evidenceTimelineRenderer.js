import { t } from './i18n.js';

import {
  buildVisualTimeline,
} from "./evidenceTimelineVisual.js";

export function renderEvidenceTimeline(events = [], currentLanguage = 'en') {
  const timeline = buildVisualTimeline(events);

  return `
    <section class="evidence-panel-card evidence-timeline-card">
      <h3>${t(currentLanguage, 'timeline.title')}</h3>

      <div class="evidence-timeline">
        ${timeline.map((event) => `
          <div class="timeline-event ${event.className}">
            <div class="timeline-icon">
              ${event.icon}
            </div>

            <div class="timeline-content">
              <strong>${event.i18nKey ? t(currentLanguage, event.i18nKey) : event.title}</strong>
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
