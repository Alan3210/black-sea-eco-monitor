import {
  renderEvidencePanelShell,
} from "./evidenceDashboardPanel.js";

export function mountEvidencePanel(container) {
  if (!container) {
    return false;
  }

  container.innerHTML = renderEvidencePanelShell();

  return true;
}
