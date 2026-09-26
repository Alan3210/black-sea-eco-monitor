from pathlib import Path
import shutil

ROOT = Path.cwd()
MAIN = ROOT / "frontend" / "src" / "main.js"

def main():
    text = MAIN.read_text(encoding="utf-8")

    backup = MAIN.with_suffix(".js.air21d3d.bak")
    if not backup.exists():
        shutil.copy2(MAIN, backup)

    old = """if (isDashboardMode()) {
  hideLegacyApplication();

  const root = createDashboardRoot();

  void mountEvidenceDashboard(root);

  return;
}
"""

    new = """if (isDashboardMode()) {
  document.body.innerHTML = '';

  const root = createDashboardRoot();

  void mountEvidenceDashboard(root);

} else {
"""

    if old in text:
        text = text.replace(old, new, 1)
        MAIN.write_text(text, encoding="utf-8")
        print("PATCH APPLIED")
    else:
        print("Manual integration required: dashboard block not found")

if __name__ == "__main__":
    main()
