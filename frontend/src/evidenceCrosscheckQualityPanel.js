export function buildEvidenceQualityPanelSection(
  source = {},
) {
  const quality = source.quality || {};

  return {
    provider: source.provider || "Unknown",
    type: source.source_type || "unknown",
    value: source.value ?? null,
    unit: source.unit || null,
    quality: {
      freshness:
        quality.freshness_seconds != null
          ? `${quality.freshness_seconds}s`
          : "Unknown",
      temporal:
        quality.temporal_alignment || "unknown",
      spatial:
        quality.spatial_alignment || "unknown",
      flags: Array.isArray(quality.quality_flags)
        ? quality.quality_flags
        : [],
    },
  };
}

export function buildEvidenceQualityPanel(
  sources = [],
) {
  return sources.map(buildEvidenceQualityPanelSection);
}
