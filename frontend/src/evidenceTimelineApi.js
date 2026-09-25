const DEFAULT_ENDPOINT = "/air/evidence-timeline";

export async function fetchEvidenceTimeline(
  fetchImpl = fetch,
  endpoint = DEFAULT_ENDPOINT,
) {
  const response = await fetchImpl(endpoint);

  if (!response.ok) {
    throw new Error(
      `Evidence timeline request failed: ${response.status}`,
    );
  }

  return response.json();
}
