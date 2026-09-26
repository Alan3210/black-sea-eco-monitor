from pathlib import Path
import shutil

ROOT = Path.cwd()
MAIN = ROOT / "frontend" / "src" / "main.js"

OLD = """if (isDashboardMode()) {
  const root = createDashboardRoot();

  void mountEvidenceDashboard(root);

  // Dashboard mode skips MapLibre bootstrap.
  throw new Error('Dashboard mode active');
}
"""

NEW = """if (isDashboardMode()) {
  hideLegacyApplication();

  const root = createDashboardRoot();

  void mountEvidenceDashboard(root);

  // Dashboard mode skips MapLibre bootstrap.
  export default null;
}
"""

def main():
    text = MAIN.read_text(encoding="utf-8")

    if OLD not in text:
        raise SystemExit("Expected dashboard block not found")

    backup = MAIN.with_suffix(".js.air21d3c_throw_fix.bak")
    shutil.copy2(MAIN, backup)

    text = text.replace(OLD, NEW, 1)

    MAIN.write_text(text, encoding="utf-8")
    print("PATCH APPLIED")

if __name__ == "__main__":
    main()
