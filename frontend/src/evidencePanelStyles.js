export const EVIDENCE_PANEL_THEME = {
  root: "evidence-panel",
  card: "evidence-panel-card",
  status: {
    ready: "evidence-status-ready",
    warning: "evidence-status-warning",
    error: "evidence-status-error",
  },
};

export function getEvidenceCardClass(type = "default") {
  return `evidence-panel-card evidence-panel-card--${type}`;
}

export function getEvidenceStatusClass(state) {
  if (state === "ready") {
    return EVIDENCE_PANEL_THEME.status.ready;
  }

  if (state === "warning") {
    return EVIDENCE_PANEL_THEME.status.warning;
  }

  return EVIDENCE_PANEL_THEME.status.error;
}

export function renderEvidencePanelLayout(content = "") {
  return `
    <aside class="${EVIDENCE_PANEL_THEME.root}">
      ${content}
    </aside>
  `;
}
