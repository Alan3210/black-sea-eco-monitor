from pathlib import Path
import shutil

ROOT = Path.cwd()
MAIN = ROOT / "frontend" / "src" / "main.js"

OLD = """if (isDashboardMode()) {
  hideLegacyApplication();

  const root = createDashboardRoot();

  void mountEvidenceDashboard(root);

  // Dashboard mode skips MapLibre bootstrap.
  export default null;
}
"""

NEW = """if (isDashboardMode()) {
  hideLegacyApplication();

  const root = createDashboardRoot();

  void mountEvidenceDashboard(root);

} else {
"""

def main():
    text = MAIN.read_text(encoding="utf-8")

    backup = MAIN.with_suffix(".js.air21d3e.bak")
    if not backup.exists():
        shutil.copy2(MAIN, backup)

    if OLD not in text:
        raise SystemExit("Expected dashboard block not found")

    text = text.replace(OLD, NEW, 1)

    MAIN.write_text(text, encoding="utf-8")
    print("DASHBOARD WRAPPER PATCH APPLIED")
    print("IMPORTANT: close the final else block at the end of main.js after map bootstrap.")

if __name__ == "__main__":
    main()
