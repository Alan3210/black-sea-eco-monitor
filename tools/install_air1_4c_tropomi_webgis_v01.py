from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "_air1_4c_payload"

MAIN = ROOT / "frontend/src/main.js"
INDEX = ROOT / "frontend/index.html"
STYLE = ROOT / "frontend/src/style.css"

MODULE_SRC = PAYLOAD / "frontend/src/tropomiOperationalField.js"
TEST_SRC = PAYLOAD / "frontend/src/tropomiOperationalField.test.js"

MODULE_DST = ROOT / "frontend/src/tropomiOperationalField.js"
TEST_DST = ROOT / "frontend/src/tropomiOperationalField.test.js"

IMPORT_LINE = (
    "import { installTropomiSatelliteLayer } "
    "from './tropomiOperationalField.js';"
)
HOST_MARKER = 'id="tropomi-air-root"'
STYLE_MARKER = "/* AIR-1.4C TROPOMI Web GIS */"

HOST_HTML = """
      <div id="tropomi-air-root" class="tropomi-air-root"></div>
"""

STYLE_BLOCK = """

/* AIR-1.4C TROPOMI Web GIS */
.tropomi-air-root {
  margin-top: 12px;
}

.tropomi-card {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 10px;
  background: rgba(13, 20, 31, 0.58);
  backdrop-filter: blur(8px);
}

.tropomi-card__head,
.tropomi-field,
.tropomi-opacity,
.tropomi-selected,
.tropomi-meta > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.tropomi-card__title {
  font-size: 12px;
  font-weight: 700;
}

.tropomi-card__subtitle,
.tropomi-hint,
.tropomi-disclaimer,
.tropomi-status {
  margin-top: 4px;
  font-size: 10px;
  line-height: 1.35;
  opacity: 0.72;
}

.tropomi-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
}

.tropomi-field,
.tropomi-opacity,
.tropomi-selected {
  margin-top: 9px;
  font-size: 10px;
}

.tropomi-field select {
  min-width: 104px;
}

.tropomi-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 5px;
  margin-top: 9px;
}

.tropomi-metrics > div {
  border-radius: 8px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.04);
}

.tropomi-metrics span,
.tropomi-metrics strong {
  display: block;
}

.tropomi-metrics span {
  font-size: 9px;
  opacity: 0.6;
}

.tropomi-metrics strong {
  margin-top: 2px;
  font-size: 10px;
}

.tropomi-legend {
  margin-top: 8px;
}

.tropomi-legend__bar {
  height: 7px;
  border-radius: 999px;
  background: linear-gradient(
    90deg,
    #31498F 0%,
    #2B8BC6 25%,
    #46B7A9 50%,
    #E6C85A 75%,
    #D76A55 100%
  );
}

.tropomi-legend__labels {
  display: flex;
  justify-content: space-between;
  margin-top: 3px;
  font-size: 9px;
  opacity: 0.72;
}

.tropomi-meta {
  display: grid;
  gap: 4px;
  margin-top: 8px;
  font-size: 10px;
}

.tropomi-opacity input[type="range"] {
  width: 84px;
}

.tropomi-selected strong {
  text-align: right;
}

.tropomi-status {
  min-height: 14px;
}

.tropomi-disclaimer {
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}
"""


def backup(path: Path, backup_root: Path) -> None:
    if not path.exists():
        return
    target = backup_root / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def patch_main(text: str) -> str:
    if IMPORT_LINE not in text:
        anchor = "from './camsAirOperationalField.js';"
        index = text.find(anchor)
        if index < 0:
            raise RuntimeError("main.js CAMS import anchor not found.")
        end = index + len(anchor)
        text = text[:end] + "\n" + IMPORT_LINE + text[end:]

    if "installTropomiSatelliteLayer(map);" not in text:
        anchor = "installCamsAirLayer();"
        index = text.find(anchor)
        if index < 0:
            raise RuntimeError(
                "main.js installCamsAirLayer() anchor not found."
            )
        line_start = text.rfind("\n", 0, index) + 1
        indent = text[line_start:index]
        end = index + len(anchor)
        text = (
            text[:end]
            + "\n"
            + indent
            + "installTropomiSatelliteLayer(map);"
            + text[end:]
        )
    return text


def patch_index(text: str) -> str:
    if HOST_MARKER in text:
        return text

    panel_anchor = 'id="cams-air-panel"'
    panel_index = text.find(panel_anchor)
    if panel_index < 0:
        raise RuntimeError("index.html CAMS panel anchor not found.")

    section_end = text.find("</section>", panel_index)
    if section_end < 0:
        raise RuntimeError(
            "index.html atmosphere </section> not found after CAMS panel."
        )

    return text[:section_end] + HOST_HTML + text[section_end:]


def patch_style(text: str) -> str:
    if STYLE_MARKER in text:
        return text
    return text.rstrip() + STYLE_BLOCK + "\n"


def main() -> int:
    required = [MAIN, INDEX, STYLE, MODULE_SRC, TEST_SRC]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("ERROR: AIR-1.4C prerequisites/payload missing:")
        for item in missing:
            print(f"  {item}")
        return 2

    main_old = MAIN.read_text(encoding="utf-8")
    index_old = INDEX.read_text(encoding="utf-8")
    style_old = STYLE.read_text(encoding="utf-8")

    try:
        main_new = patch_main(main_old)
        index_new = patch_index(index_old)
        style_new = patch_style(style_old)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        print("No production files modified.")
        return 3

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = (
        ROOT / "dev-snapshots" / f"air1_4c_before_apply_{stamp}"
    )

    for path in [MAIN, INDEX, STYLE, MODULE_DST, TEST_DST]:
        backup(path, backup_root)

    MODULE_DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(MODULE_SRC, MODULE_DST)
    shutil.copy2(TEST_SRC, TEST_DST)

    MAIN.write_text(main_new, encoding="utf-8", newline="\n")
    INDEX.write_text(index_new, encoding="utf-8", newline="\n")
    STYLE.write_text(style_new, encoding="utf-8", newline="\n")

    verify_main = MAIN.read_text(encoding="utf-8")
    verify_index = INDEX.read_text(encoding="utf-8")
    verify_style = STYLE.read_text(encoding="utf-8")

    if (
        IMPORT_LINE not in verify_main
        or "installTropomiSatelliteLayer(map);" not in verify_main
        or HOST_MARKER not in verify_index
        or STYLE_MARKER not in verify_style
    ):
        print("ERROR: AIR-1.4C verification failed.")
        return 4

    shutil.rmtree(PAYLOAD)

    print("AIR-1.4C TROPOMI Web GIS v0.1 installed.")
    print("REAL frontend mutation: APPLIED")
    print("Layer source: GET /air/satellite-field")
    print("Default product: NO2")
    print("Default satellite stride: 2")
    print("Latest-available lookback: 7 days")
    print("Visualization: valid satellite cells only")
    print("Scale: relative P5/P25/P50/P75/P95")
    print("Display units: mol/m2 -> micromol/m2 for readability")
    print("Semantics shown in UI: column retrieval, NOT surface concentration")
    print("Map click: exact selected-cell value in panel")
    print("Added:")
    print("  frontend\\src\\tropomiOperationalField.js")
    print("  frontend\\src\\tropomiOperationalField.test.js")
    print("Modified:")
    print("  frontend\\index.html")
    print("  frontend\\src\\main.js")
    print("  frontend\\src\\style.css")
    print("Backup:")
    print(backup_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
