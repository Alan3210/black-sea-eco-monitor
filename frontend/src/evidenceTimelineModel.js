export function buildEvidenceTimelineModel(
  timeline = {},
) {
  return {
    pollutant: timeline.pollutant || "Unknown",
    series: Array.isArray(timeline.series)
      ? timeline.series.map((item) => ({
          source: item.source || "Unknown",
          sourceType: item.source_type || "unknown",
          points: Array.isArray(item.points)
            ? item.points
            : [],
        }))
      : [],
  };
}
