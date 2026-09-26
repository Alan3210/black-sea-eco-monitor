import {
  renderEvidencePanelShell,
} from "./evidenceDashboardPanel.js";

export function mountEvidencePanel(container) {
  if (!container) {
    return false;
  }

  container.innerHTML = renderEvidencePanelShell();

const panel = container.querySelector("#evidence-panel");

if (panel) {
  panel.style.display = "none";
}

return true;
}
