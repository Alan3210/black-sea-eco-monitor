import {
  renderEvidencePanel,
} from "./evidencePanelRenderer.js";

export function mountEvidencePanelContent(
  container,
  payload = {},
) {
  if (!container) {
    return false;
  }

  container.innerHTML = renderEvidencePanel(payload);

  const panel = container.closest("#evidence-panel");

  if (panel) {
    panel.style.display = "";
  }

  return true;
}