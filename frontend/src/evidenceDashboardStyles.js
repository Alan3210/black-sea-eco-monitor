export const EVIDENCE_DASHBOARD_THEME = {
  cardClass: "evidence-card",
  gridClass: "evidence-dashboard-grid",
  status: {
    ready: "status-ready",
    warning: "status-warning",
    error: "status-error",
  },
};

export function getDashboardCardClass(type = "default") {
  return `evidence-card evidence-card--${type}`;
}

export function getStatusClass(available) {
  return available
    ? EVIDENCE_DASHBOARD_THEME.status.ready
    : EVIDENCE_DASHBOARD_THEME.status.error;
}
