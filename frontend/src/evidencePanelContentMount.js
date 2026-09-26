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

  return true;
}
