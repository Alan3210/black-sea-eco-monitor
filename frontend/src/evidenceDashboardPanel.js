export function createEvidencePanelState() {
  return {
    visible: false,
    selectedEventId: null,
  };
}

export function openEvidencePanel(state, eventId = null) {
  return {
    ...state,
    visible: true,
    selectedEventId: eventId,
  };
}

export function closeEvidencePanel(state) {
  return {
    ...state,
    visible: false,
    selectedEventId: null,
  };
}

export function renderEvidencePanelShell() {
  return `
    <aside id="evidence-panel" class="evidence-panel">
      <div class="evidence-panel__header">
        <h2>Evidence Dashboard</h2>
      </div>
      <div id="evidence-panel-content"></div>
    </aside>
  `;
}
