export const TIMELINE_EVENT_TYPES = {
  observation: {
    icon: "🛰",
    className: "timeline-observation",
    i18nKey: "timeline.satelliteObservation",
  },
  model: {
    icon: "🌍",
    className: "timeline-model",
    i18nKey: "timeline.camsForecast",
  },
  detection: {
    icon: "🔥",
    className: "timeline-detection",
    i18nKey: "timeline.eventDetected",
  },
  confirmation: {
    icon: "📡",
    className: "timeline-confirmation",
    i18nKey: "timeline.evidenceUpdate",
  },
};

export function getTimelineEventVisual(type) {
  return (
    TIMELINE_EVENT_TYPES[type] ||
    {
      icon: "•",
      className: "timeline-default",
    }
  );
}

export function buildVisualTimeline(events = []) {
  return events.map((event) => {
    const visual = getTimelineEventVisual(event.type);

    return {
      ...event,
      icon: visual.icon,
      className: visual.className,
      i18nKey: visual.i18nKey,
    };
  });
}
