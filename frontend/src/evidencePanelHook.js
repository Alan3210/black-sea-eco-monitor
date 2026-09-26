import {
  mountLiveEvidencePanel,
} from "./liveEvidencePanel.js";

export function createEvidencePanelMountPoint() {
  const existing = document.getElementById(
    "evidence-panel-root",
  );

  if (existing) {
    return existing;
  }

  const root = document.createElement("div");
  root.id = "evidence-panel-root";

  document.body.appendChild(root);

  return root;
}

export function mountEvidencePanelToMapUI() {
  const root = createEvidencePanelMountPoint();

  return mountLiveEvidencePanel(root);
}
