export function buildEvidenceDashboardPageModel(
  data = {},
) {
  return {
    title: "Evidence Dashboard",
    sections: [
      {
        id: "summary",
        title: "Sources Status",
        data: data.summary || {},
      },
      {
        id: "timeline",
        title: "Timeline",
        data: data.timeline || {},
      },
      {
        id: "quality",
        title: "Quality Overview",
        data: data.quality || {},
      },
      {
        id: "crosscheck",
        title: "Evidence Crosscheck",
        data: data.crosscheck || {},
      },
    ],
  };
}
