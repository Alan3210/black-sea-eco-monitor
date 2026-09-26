export function extractEventTimeline(event = {}) {
  return Array.isArray(event.timeline)
    ? event.timeline
    : [];
}

export function normalizeEventTimeline(event = {}) {
  return extractEventTimeline(event).map((item) => ({
    type: item.type || "evidence",
    title: item.title || "Evidence event",
    source: item.source || "",
    time: item.time || "",
  }));
}

export function hasRealTimeline(event = {}) {
  return normalizeEventTimeline(event).length > 0;
}
