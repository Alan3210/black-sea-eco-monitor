export function buildInvestigationViewModel(
  investigation = {},
) {
  const evidence = Array.isArray(
    investigation.evidence,
  )
    ? investigation.evidence
    : [];

  const evidenceByType = evidence.reduce(
    (groups, record) => {
      const type =
        record.type || 'unknown';

      if (!groups[type]) {
        groups[type] = [];
      }

      groups[type].push(record);

      return groups;
    },
    {},
  );

  const candidateSources =
    Array.isArray(
      investigation.candidateSources,
    )
      ? investigation.candidateSources
      : [];

  return {
    eventId:
      investigation.eventId ?? null,

    evidence,

    evidenceCount:
      evidence.length,

    evidenceByType,

    evidenceTypes:
      Object.keys(evidenceByType),

    candidateSources,

    candidateSourceCount:
      candidateSources.length,

    hasEvidence:
      evidence.length > 0,
  };
}