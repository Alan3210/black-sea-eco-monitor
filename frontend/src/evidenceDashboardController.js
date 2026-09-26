import { fetchDashboardData } from "./evidenceDashboardApi.js";
import { buildEvidenceDashboardModel } from "./evidenceDashboardModel.js";


export async function loadEvidenceDashboard(
  fetchImpl = fetch,
) {
  const data = await fetchDashboardData(fetchImpl);

  return buildEvidenceDashboardModel(data);
}
