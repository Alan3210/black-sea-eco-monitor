import { loadEvidenceDashboard } from "./evidenceDashboardController.js";
import { renderEvidenceDashboardHTML } from "./evidenceDashboardRenderer.js";

export async function mountEvidenceDashboard(
  container,
  fetchImpl = fetch,
) {
  const model = await loadEvidenceDashboard(fetchImpl);

  container.innerHTML =
    renderEvidenceDashboardHTML(model);

  return model;
}

export function shouldOpenDashboard(
  hash = window.location.hash,
) {
  return hash === "#dashboard";
}
