export function buildEvidenceCrosscheckPanelModel(
  crosscheck = {},
) {
  const sources = Array.isArray(crosscheck.sources)
    ? crosscheck.sources.map((source) => ({
        provider: source.provider || "Unknown",
        type: source.source_type || "unknown",
        pollutant: source.pollutant || null,
        value: source.value ?? null,
        unit: source.unit || null,
      }))
    : [];

  const pollutants = [
    ...new Set(
      sources
        .map((source) => source.pollutant)
        .filter(Boolean),
    ),
  ];

  return {
    title: "Evidence Crosscheck",
    location: crosscheck.position || null,
    timestamp: crosscheck.observed_at || null,
    sources,
    pollutants,
  };
}
