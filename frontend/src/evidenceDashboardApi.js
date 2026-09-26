const DEFAULT_ENDPOINTS = {
  summary: "/air/evidence-summary",
  timeline: "/air/evidence-timeline",
  crosscheck: "/air/evidence-crosscheck",
};

async function fetchJSON(fetchImpl, endpoint) {
  const response = await fetchImpl(endpoint);

  if (!response.ok) {
    throw new Error(
      `Dashboard request failed: ${response.status}`,
    );
  }

  return response.json();
}

export async function fetchDashboardData(
  fetchImpl = fetch,
  endpoints = DEFAULT_ENDPOINTS,
) {
  const [summary, timeline, crosscheck] =
    await Promise.all([
      fetchJSON(fetchImpl, endpoints.summary),
      fetchJSON(fetchImpl, endpoints.timeline),
      fetchJSON(fetchImpl, endpoints.crosscheck),
    ]);

  return {
    summary,
    timeline,
    crosscheck,
    quality: crosscheck.quality || {},
  };
}
