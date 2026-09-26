from pathlib import Path
import shutil

ROOT = Path.cwd()

MAIN = ROOT / "frontend" / "src" / "main.js"

IMPORT_MARKER = "import './style.css';"

IMPORT_BLOCK = """
import {
  isDashboardMode,
  createDashboardRoot,
} from './evidenceDashboardMode.js';

import {
  mountEvidenceDashboard,
} from './evidenceDashboardEntry.js';
"""

BOOT_MARKER = "const map = new maplibregl.Map"

BOOT_BLOCK = """
if (isDashboardMode()) {
  const root = createDashboardRoot();

  void mountEvidenceDashboard(root);

  // Dashboard mode skips MapLibre bootstrap.
  throw new Error('Dashboard mode active');
}

"""

def main():
    text = MAIN.read_text(encoding="utf-8")

    if "evidenceDashboardMode.js" not in text:
        text = text.replace(
            IMPORT_MARKER,
            IMPORT_MARKER + IMPORT_BLOCK,
            1,
        )

    if "Dashboard mode skips MapLibre bootstrap" not in text:
        text = text.replace(
            BOOT_MARKER,
            BOOT_BLOCK + BOOT_MARKER,
            1,
        )

    backup = MAIN.with_suffix(".js.air21d3b.bak")
    if not backup.exists():
        shutil.copy2(MAIN, backup)

    MAIN.write_text(text, encoding="utf-8")

    print("MAIN.JS PATCH APPLIED")

if __name__ == "__main__":
    main()
