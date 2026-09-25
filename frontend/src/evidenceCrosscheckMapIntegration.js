export function findEvidenceTargetFromFeature(
  feature = {},
) {
  return {
    latitude:
      feature.properties?.latitude ??
      feature.geometry?.coordinates?.[1] ??
      null,
    longitude:
      feature.properties?.longitude ??
      feature.geometry?.coordinates?.[0] ??
      null,
  };
}

export function createEvidenceCrosscheckClickHandler(
  loadEvidence,
  renderPanel,
) {
  return async (event) => {
    const target = findEvidenceTargetFromFeature(
      event?.features?.[0] || {},
    );

    const evidence = await loadEvidence(target);

    return renderPanel(evidence);
  };
}
