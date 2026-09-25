export function renderEvidenceTimelineHTML(
  viewModel = {},
) {
  const seriesHTML = (viewModel.series || [])
    .map((series) => {
      const points = (series.points || [])
        .map(
          (point) =>
            `<div class="timeline-point">${point.time || ""}: ${point.value ?? ""}</div>`,
        )
        .join("");

      return `
        <section class="timeline-series">
          <h4>${series.label}</h4>
          <div class="timeline-type">${series.type}</div>
          ${points}
        </section>
      `;
    })
    .join("");

  return `
    <div class="timeline-panel">
      <h3>${viewModel.title || "Timeline"}</h3>
      ${seriesHTML}
    </div>
  `;
}
