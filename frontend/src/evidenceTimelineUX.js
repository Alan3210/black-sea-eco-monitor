import { t } from './i18n.js';

export const TIMELINE_VISUAL_STATES = {
  observation: {
    icon: "🛰",
    colorClass: "timeline-source-observation",
  },
  model: {
    icon: "🌍",
    colorClass: "timeline-source-model",
  },
  detection: {
    icon: "🔥",
    colorClass: "timeline-source-detection",
  },
  confirmation: {
    icon: "📡",
    colorClass: "timeline-source-confirmation",
  },
};

export function buildTimelineCard(event = {}) {
  const visual =
    TIMELINE_VISUAL_STATES[event.type] ||
    {
      icon: "•",
      colorClass: "timeline-source-default",
    };

  return {
    ...event,
    icon: visual.icon,
    colorClass: visual.colorClass,
  };
}

export function buildVerticalTimeline(events = []) {
  return events.map(buildTimelineCard);
}

export function renderVerticalTimeline(
  events = [],
  currentLanguage = 'ru'
) {
  const cards = buildVerticalTimeline(events);

return `
  ${cards.map((event) => `
    <article class="timeline-card ${event.colorClass}">
      <div class="timeline-card__icon">
        ${event.icon}
      </div>

      <div class="timeline-card__body">
        <strong>${
          event.i18nKey
            ? t(currentLanguage, event.i18nKey)
            : event.title || "Evidence event"
        }</strong>
        <span>${event.time || ""}</span>
        ${
          event.source
            ? `<small>${event.source}</small>`
            : ""
        }
      </div>
    </article>
  `).join("")}
`;
}
