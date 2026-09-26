export function createOperatorDashboardState() {
  return {
    mapReady: false,
    panelReady: false,
    selectedEventId: null,
    evidenceLoaded: false,
  };
}

export function markMapReady(state) {
  return {
    ...state,
    mapReady: true,
  };
}

export function markPanelReady(state) {
  return {
    ...state,
    panelReady: true,
  };
}

export function selectOperatorEvent(state, eventId) {
  return {
    ...state,
    selectedEventId: eventId,
  };
}

export function markEvidenceLoaded(state) {
  return {
    ...state,
    evidenceLoaded: true,
  };
}
