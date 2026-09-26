export function buildDashboardLayoutModel(
  dashboard = {},
) {
  return {
    title: dashboard.title || "Evidence Dashboard",

    layout: [
      {
        id: "top",
        columns: [
          {
            id: "summary",
            component: "SourcesStatus",
          },
          {
            id: "quality",
            component: "QualityOverview",
          },
        ],
      },
      {
        id: "timeline",
        columns: [
          {
            id: "timeline",
            component: "EvidenceTimeline",
          },
        ],
      },
      {
        id: "crosscheck",
        columns: [
          {
            id: "crosscheck",
            component: "EvidenceCrosscheck",
          },
        ],
      },
    ],
  };
}
