export const TIMELINE_EVENT_TYPES = {
  observation: {
    icon: "🛰",
    className: "timeline-observation",
  },
  model: {
    icon: "🌍",
    className: "timeline-model",
  },
  detection: {
    icon: "🔥",
    className: "timeline-detection",
  },
  confirmation: {
    icon: "📡",
    className: "timeline-confirmation",
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
    };
  });
}
