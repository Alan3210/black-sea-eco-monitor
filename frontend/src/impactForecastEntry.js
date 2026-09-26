export function createImpactForecastState({
  loading = false,
  available = false,
  error = null,
} = {}) {
  return {
    loading,
    available,
    error,
    action: loading
      ? "running"
      : available
        ? "recalculate"
        : "run",
  };
}

export function getImpactForecastButtonLabel(state = {}) {
  if (state.loading) {
    return "Running forecast...";
  }

  if (state.available) {
    return "Recalculate forecast";
  }

  return "Run Impact Forecast";
}
