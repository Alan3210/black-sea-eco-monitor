export function renderEvidenceQualityHTML(
  quality = {},
) {
  const flags = Array.isArray(quality.flags) &&
    quality.flags.length
    ? quality.flags.join(", ")
    : "none";

  return `
    <div class="evidence-quality-block">
      <h4>Data Quality</h4>

      <div>
        <b>Freshness:</b> ${quality.freshness || "Unknown"}
      </div>

      <div>
        <b>Temporal:</b> ${quality.temporal || "unknown"}
      </div>

      <div>
        <b>Spatial:</b> ${quality.spatial || "unknown"}
      </div>

      <div>
        <b>Flags:</b> ${flags}
      </div>
    </div>
  `;
}
