const DEFAULT_ENDPOINT =
  "/air/evidence-crosscheck";

export async function fetchEvidenceForEvent(
  eventId,
  fetchImpl = fetch,
) {
  if (!eventId) {
    return null;
  }

  const response = await fetchImpl(
    `${DEFAULT_ENDPOINT}?event_id=${encodeURIComponent(eventId)}`,
  );

  if (!response.ok) {
    throw new Error(
      `Evidence request failed: ${response.status}`,
    );
  }

  return response.json();
}
