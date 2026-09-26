export function normalizeEvidenceTimelineEvents(
  events = [],
) {
  return events
    .filter((event) => event && event.time)
    .map((event) => ({
      time: event.time,
      type: event.type || "evidence",
      title: event.title || "Evidence update",
      source: event.source || null,
    }));
}

export function buildEvidenceEventTimeline(
  events = [],
) {
  return {
    title: "Evidence Timeline",
    events: normalizeEvidenceTimelineEvents(events),
  };
}

export function renderEvidenceEventTimeline(
  timeline = {},
) {
  return `
    <section class="evidence-panel-card evidence-timeline-card">
      <h3>${timeline.title || "Evidence Timeline"}</h3>
      <ol>
        ${(timeline.events || []).map((event) => `
          <li>
            <strong>${event.title}</strong>
            <span>${event.time}</span>
            ${event.source ? `<small>${event.source}</small>` : ""}
          </li>
        `).join("")}
      </ol>
    </section>
  `;
}
