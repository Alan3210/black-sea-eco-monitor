export function createTimelineContainer(
  renderer,
  events = [],
) {
  return renderer(events);
}

export function hasSingleTimelineRoot(html = "") {
  const matches = html.match(
    /evidence-vertical-timeline/g,
  ) || [];

  return matches.length === 1;
}
