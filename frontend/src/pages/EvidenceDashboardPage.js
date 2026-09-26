import { buildEvidenceDashboardModel } from "../evidenceDashboardModel.js";
import { buildDashboardLayoutModel } from "../EvidenceDashboardLayout.js";

export function buildEvidenceDashboardPage(data = {}) {
  const model = buildEvidenceDashboardModel(data);
  const layout = buildDashboardLayoutModel(model);

  return {
    model,
    layout,
    route: "/dashboard/evidence",
  };
}
