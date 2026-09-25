const DEFAULT_ENDPOINT = "/air/evidence-crosscheck";

export async function fetchEvidenceCrosscheck(
  fetchImpl = fetch,
  endpoint = DEFAULT_ENDPOINT,
) {
  const response = await fetchImpl(endpoint);

  if (!response.ok) {
    throw new Error(
      `Evidence crosscheck request failed: ${response.status}`,
    );
  }

  return normalizeEvidenceCrosscheck(
    await response.json(),
  );
}

export function normalizeEvidenceCrosscheck(
  payload = {},
) {
  return {
    position: payload.position || null,
    observed_at: payload.observed_at || null,
    sources: Array.isArray(payload.sources)
      ? payload.sources.map((source) => ({
          provider: source.provider || null,
          source_type: source.source_type || null,
          pollutant: source.pollutant || null,
          value: source.value ?? null,
          unit: source.unit || null,
        }))
      : [],
  };
}
