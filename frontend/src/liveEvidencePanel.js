import {
  mountEvidencePanel,
} from "./evidencePanelMount.js";

import {
  createEvidencePanelState,
} from "./evidenceDashboardPanel.js";


export function createLiveEvidencePanel() {
  return {
    state: createEvidencePanelState(),
    mounted: false,
  };
}


export function mountLiveEvidencePanel(
  container,
  panel = createLiveEvidencePanel(),
) {
  panel.mounted = mountEvidencePanel(container);

  return panel;
}


export function setEvidencePanelEvent(
  panel,
  eventId,
) {
  return {
    ...panel,
    state: {
      ...panel.state,
      visible: true,
      selectedEventId: eventId,
    },
  };
}
