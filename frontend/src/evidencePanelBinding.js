import {
  openEvidencePanel,
} from "./evidenceDashboardPanel.js";

export function selectEvidenceEvent(
  state,
  eventId,
) {
  return openEvidencePanel(
    state,
    eventId,
  );
}

export function buildEvidencePanelRequest(
  eventId,
) {
  if (!eventId) {
    return null;
  }

  return {
    endpoint: "/air/evidence-crosscheck",
    params: {
      event_id: eventId,
    },
  };
}

export function updateEvidencePanelContent(
  container,
  payload,
) {
  if (!container) {
    return false;
  }

  container.innerHTML = `
    <div class="evidence-panel-event">
      <h3>Evidence Event</h3>
      <pre>${JSON.stringify(
        payload || {},
        null,
        2,
      )}</pre>
    </div>
  `;

  return true;
}
