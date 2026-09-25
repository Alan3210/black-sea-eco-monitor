export function buildEvidenceDashboardModel(
  {
    summary = {},
    timeline = {},
    quality = {},
  } = {},
) {
  return {
    title: "Evidence Dashboard",

    summary: {
      sources: summary.sources || {},
      quality: summary.quality || {},
    },

    timeline: {
      pollutant: timeline.pollutant || "Unknown",
      series: Array.isArray(timeline.series)
        ? timeline.series
        : [],
    },

    quality: {
      records: quality.records || [],
    },
  };
}
