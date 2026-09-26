export function buildDriftVisualizationState(payload = {}) {
  return {
    available: Boolean(payload && Object.keys(payload).length),
    visible: Boolean(payload?.visible),
    envelope: payload?.envelope || null,
    track: payload?.track || null,
  };
}

export function shouldShowDriftLayer(state = {}) {
  return Boolean(
    state.available
    && state.visible,
  );
}
