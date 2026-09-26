export function buildDashboardStructure(model = {}) {
  return {
    title: model.title || "Evidence Dashboard",

    cards: [
      {
        id: "sources",
        title: "Sources Status",
        type: "status",
        data: model.summary || {},
      },
      {
        id: "quality",
        title: "Quality Overview",
        type: "quality",
        data: model.quality || {},
      },
      {
        id: "timeline",
        title: "Evidence Timeline",
        type: "timeline",
        data: model.timeline || {},
      },
      {
        id: "crosscheck",
        title: "Evidence Crosscheck",
        type: "crosscheck",
        data: model.crosscheck || {},
      },
    ],
  };
}
