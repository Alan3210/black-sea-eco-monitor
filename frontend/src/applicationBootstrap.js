import {
  isDashboardMode,
  createDashboardRoot,
} from "./evidenceDashboardMode.js";

import {
  mountEvidenceDashboard,
} from "./evidenceDashboardEntry.js";


export async function bootstrapApplication({
  startMapApplication,
} = {}) {
  if (isDashboardMode()) {
    const root = createDashboardRoot();

    await mountEvidenceDashboard(root);

    return "dashboard";
  }

  if (typeof startMapApplication === "function") {
    await startMapApplication();
  }

  return "map";
}
