export function isDashboardMode(
  hash = typeof window !== "undefined"
    ? window.location.hash
    : "",
) {
  return hash === "#dashboard";
}

export function createDashboardRoot() {
  const existing = document.getElementById(
    "evidence-dashboard-root",
  );

  if (existing) {
    return existing;
  }

  document.body.innerHTML = "";

  const root = document.createElement("div");
  root.id = "evidence-dashboard-root";

  document.body.appendChild(root);

  return root;
}

export function hideLegacyApplication() {
  const app = document.getElementById("app");

  if (app) {
    app.style.display = "none";
  }
}
