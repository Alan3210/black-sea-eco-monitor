export function normalizeTimelineEvent(event = {}) {
  return {
    type: event.type || "evidence",
    title: event.title || "Evidence event",
    source: event.source || "—",
    time: event.time || "—",
  };
}

export function buildTimelineEmptyState(events = []) {
  if (!events.length) {
    return {
      empty: true,
      message: "No timeline events available",
    };
  }

  return {
    empty: false,
    events: events.map(normalizeTimelineEvent),
  };
}

export function buildTimelineSourceLink(event = {}) {
  return {
    source: event.source || "—",
    title: event.title || "Evidence event",
  };
}
