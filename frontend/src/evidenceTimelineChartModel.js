export function buildEvidenceTimelineChartModel(
  viewModel = {},
) {
  const series = (viewModel.series || []).map((item) => ({
    label: item.label,
    type: item.type,
    points: item.points || [],
  }));

  const allPoints = series.flatMap(
    (item) => item.points,
  );

  return {
    title: viewModel.title || "Timeline",
    pollutant: viewModel.pollutant || "Unknown",
    series,
    axes: {
      x: "time",
      y: "value",
    },
    pointCount: allPoints.length,
  };
}
