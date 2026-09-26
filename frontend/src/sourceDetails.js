export function buildSourceDetails(source = {}) {
  return {
    id: source.id || null,
    name: source.name || "Unknown source",
    type: source.type || "unknown",
    purpose: source.purpose || "",
    status: source.status || "available",
    lastUpdate: source.lastUpdate || "—",
    relatedEvidence: source.relatedEvidence ?? 0,
  };
}

export function renderSourceDetails(source = {}) {
  return `
    <section class="source-details">
      <h2>Source Details</h2>

      <div>Name: ${source.name}</div>
      <div>Type: ${source.type}</div>
      <div>Purpose: ${source.purpose}</div>
      <div>Status: ${source.status}</div>
      <div>Last update: ${source.lastUpdate}</div>
      <div>
        Related evidence:
        ${source.relatedEvidence}
      </div>
    </section>
  `;
}
