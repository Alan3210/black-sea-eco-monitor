export function buildEvidenceCrosscheckViewModel(
  panel = {},
) {
  const sections = (panel.sources || []).map((source) => ({
    provider: source.provider || "Unknown",
    type: source.type || "unknown",
    rows: [
      {
        label: "Pollutant",
        value: source.pollutant || "Unknown",
      },
      {
        label: "Value",
        value:
          source.value !== null && source.value !== undefined
            ? `${source.value} ${source.unit || ""}`.trim()
            : "Unknown",
      },
    ],
  }));

  return {
    title: panel.title || "Evidence Crosscheck",
    location: panel.location || null,
    timestamp: panel.timestamp || null,
    sections,
  };
}
