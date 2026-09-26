from pathlib import Path
import shutil

ROOT = Path.cwd()
TARGET = ROOT / "frontend" / "src" / "evidenceDashboardMode.js"

def main():
    backup = TARGET.with_suffix(".js.air21d4.bak")
    shutil.copy2(TARGET, backup)

    text = TARGET.read_text(encoding="utf-8")

    old = """export function createDashboardRoot() {
  const existing = document.getElementById(
    "evidence-dashboard-root",
  );

  if (existing) {
    return existing;
  }

  const root = document.createElement("div");
  root.id = "evidence-dashboard-root";

  document.body.appendChild(root);

  return root;
}
"""

    new = """export function createDashboardRoot() {
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
"""

    if old not in text:
        raise SystemExit("Expected createDashboardRoot block not found")

    TARGET.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("DASHBOARD CLEAN VIEW PATCH APPLIED")

if __name__ == "__main__":
    main()
