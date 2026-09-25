export function buildEvidenceTimelineViewModel(
  timeline = {},
) {
  const series = Array.isArray(timeline.series)
    ? timeline.series.map((item) => ({
        label: item.source || "Unknown",
        type: item.source_type || "unknown",
        points: Array.isArray(item.points)
          ? item.points.map((point) => ({
              time: point.time || point.timestamp || null,
              value: point.value ?? null,
            }))
          : [],
      }))
    : [];

  const timestamps = series
    .flatMap((item) => item.points.map((point) => point.time))
    .filter(Boolean);

  return {
    title: `${timeline.pollutant || "Unknown"} Timeline`,
    pollutant: timeline.pollutant || "Unknown",
    series,
    timeRange: {
      start: timestamps.length ? timestamps[0] : null,
      end: timestamps.length ? timestamps[timestamps.length - 1] : null,
    },
  };
}
