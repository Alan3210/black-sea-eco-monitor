export async function fetchInvestigation(
  href,
  fetchImpl = fetch,
) {
  if (!href) {
    return null;
  }

  const response = await fetchImpl(href, {
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    throw new Error(
      `Investigation API returned HTTP ${response.status}`,
    );
  }

  return response.json();
}