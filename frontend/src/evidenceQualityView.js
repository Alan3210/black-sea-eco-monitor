export function buildEvidenceQualityViewModel(
  quality = {},
) {
  return {
    freshness: quality.freshness_seconds != null
      ? `${quality.freshness_seconds}s`
      : "Unknown",

    temporalAlignment:
      quality.temporal_alignment || "unknown",

    spatialAlignment:
      quality.spatial_alignment || "unknown",

    flags: Array.isArray(quality.quality_flags)
      ? quality.quality_flags
      : [],
  };
}
