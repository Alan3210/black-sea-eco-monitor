export function renderEvidenceCrosscheckHTML(
  viewModel = {},
) {
  const sections = (viewModel.sections || [])
    .map(
      (section) => `
        <section class="evidence-source">
          <h4>${section.provider}</h4>
          <div class="evidence-type">${section.type}</div>
          ${
            (section.rows || [])
              .map(
                (row) =>
                  `<div class="evidence-row"><b>${row.label}:</b> ${row.value}</div>`,
              )
              .join("")
          }
        </section>
      `,
    )
    .join("");

  return `
    <div class="evidence-panel">
      <h3>${viewModel.title || "Evidence Crosscheck"}</h3>
      ${sections}
    </div>
  `;
}
