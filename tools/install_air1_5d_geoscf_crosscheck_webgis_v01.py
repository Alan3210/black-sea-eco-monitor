from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "_air1_5d_payload"

MAIN = ROOT / "frontend/src/main.js"
INDEX = ROOT / "frontend/index.html"
STYLE = ROOT / "frontend/src/style.css"

MODULE_SRC = PAYLOAD / "frontend/src/geosCfOperationalField.js"
TEST_SRC = PAYLOAD / "frontend/src/geosCfOperationalField.test.js"

MODULE_DST = ROOT / "frontend/src/geosCfOperationalField.js"
TEST_DST = ROOT / "frontend/src/geosCfOperationalField.test.js"

IMPORT_LINE = (
    "import { installGeosCfAirLayer } "
    "from './geosCfOperationalField.js';"
)
TROPOMI_IMPORT_ANCHOR = "from './tropomiOperationalField.js';"
TROPOMI_CALL_ANCHOR = "installTropomiSatelliteLayer(map);"
GEOS_CALL = "installGeosCfAirLayer(map);"

TROPOMI_ROOT = '<div id="tropomi-air-root" class="tropomi-air-root"></div>'
GEOS_ROOT = '<div id="geos-cf-air-root" class="geos-cf-air-root"></div>'
DRIFT_ANCHOR = '<div class="drift-control">'
STYLE_MARKER = "/* AIR-1.5D GEOS-CF Web GIS */"

STYLE_BLOCK = """

/* AIR-1.5D GEOS-CF Web GIS */
.geos-cf-air-root {
  margin-top: 12px;
}

.geos-cf-card,
.geos-crosscheck-card {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 10px;
  background: rgba(13, 20, 31, 0.58);
  backdrop-filter: blur(8px);
}

.geos-crosscheck-card {
  margin-top: 8px;
}

.geos-cf-card__head,
.geos-cf-field,
.geos-cf-opacity,
.geos-cf-selected,
.geos-cf-meta > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.geos-cf-card__title,
.geos-crosscheck-card__title {
  font-size: 12px;
  font-weight: 700;
}

.geos-cf-card__subtitle,
.geos-crosscheck-card__subtitle,
.geos-cf-hint,
.geos-cf-status,
.geos-cf-disclaimer,
.geos-crosscheck-status,
.geos-crosscheck-note {
  margin-top: 4px;
  font-size: 10px;
  line-height: 1.35;
  opacity: 0.72;
}

.geos-cf-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
}

.geos-cf-field,
.geos-cf-opacity,
.geos-cf-selected {
  margin-top: 9px;
  font-size: 10px;
}

.geos-cf-field select {
  min-width: 104px;
}

.geos-cf-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 5px;
  margin-top: 9px;
}

.geos-cf-metrics > div,
.geos-crosscheck-grid > div {
  border-radius: 8px;
  padding: 6px;
  background: rgba(255, 255, 255, 0.04);
}

.geos-cf-metrics span,
.geos-cf-metrics strong,
.geos-crosscheck-grid span,
.geos-crosscheck-grid strong {
  display: block;
}

.geos-cf-metrics span,
.geos-crosscheck-grid span {
  font-size: 9px;
  opacity: 0.6;
}

.geos-cf-metrics strong,
.geos-crosscheck-grid strong {
  margin-top: 2px;
  font-size: 10px;
}

.geos-cf-legend {
  margin-top: 8px;
}

.geos-cf-legend__bar {
  height: 7px;
  border-radius: 999px;
  background: linear-gradient(
    90deg,
    #40539C 0%,
    #2A86B8 25%,
    #45B3A0 50%,
    #E5C85E 75%,
    #D36B58 100%
  );
}

.geos-cf-legend__labels {
  display: flex;
  justify-content: space-between;
  margin-top: 3px;
  font-size: 9px;
  opacity: 0.72;
}

.geos-cf-meta {
  display: grid;
  gap: 4px;
  margin-top: 8px;
  font-size: 10px;
}

.geos-cf-opacity input[type="range"] {
  width: 84px;
}

.geos-cf-selected strong {
  text-align: right;
}

.geos-cf-status,
.geos-crosscheck-status {
  min-height: 14px;
}

.geos-cf-disclaimer,
.geos-crosscheck-note {
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.geos-crosscheck-button {
  width: 100%;
  margin-top: 9px;
  min-height: 32px;
}

.geos-crosscheck-button:disabled {
  opacity: 0.55;
  cursor: wait;
}

.geos-crosscheck-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px;
  margin-top: 8px;
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
        anchor_pos = text.find(TROPOMI_IMPORT_ANCHOR)
        if anchor_pos < 0:
            raise RuntimeError("TROPOMI import anchor not found in main.js.")
        end = anchor_pos + len(TROPOMI_IMPORT_ANCHOR)
        text = text[:end] + "\n" + IMPORT_LINE + text[end:]

    if GEOS_CALL not in text:
        anchor_pos = text.find(TROPOMI_CALL_ANCHOR)
        if anchor_pos < 0:
            raise RuntimeError("TROPOMI install call anchor not found in main.js.")
        line_start = text.rfind("\n", 0, anchor_pos) + 1
        indent = text[line_start:anchor_pos]
        end = anchor_pos + len(TROPOMI_CALL_ANCHOR)
        text = text[:end] + "\n" + indent + GEOS_CALL + text[end:]

    return text


def patch_index(text: str) -> str:
    if GEOS_ROOT in text:
        return text

    tropomi_pos = text.find(TROPOMI_ROOT)
    drift_pos = text.find(DRIFT_ANCHOR)

    if tropomi_pos < 0:
        raise RuntimeError("TROPOMI root anchor not found in index.html.")
    if drift_pos < 0:
        raise RuntimeError("Drift anchor not found in index.html.")
    if not tropomi_pos < drift_pos:
        raise RuntimeError("Unexpected DOM order: TROPOMI must precede Drift.")

    insertion_pos = tropomi_pos + len(TROPOMI_ROOT)
    line_start = text.rfind("\n", 0, tropomi_pos) + 1
    indent = text[line_start:tropomi_pos]

    insertion = (
        "\n\n"
        + indent
        + '<div id="geos-cf-air-root" class="geos-cf-air-root"></div>'
    )

    result = text[:insertion_pos] + insertion + text[insertion_pos:]

    geos_pos = result.find(GEOS_ROOT)
    drift_pos = result.find(DRIFT_ANCHOR)
    if not tropomi_pos < geos_pos < drift_pos:
        raise RuntimeError("GEOS-CF placement verification failed.")

    return result


def patch_style(text: str) -> str:
    if STYLE_MARKER in text:
        return text
    return text.rstrip() + STYLE_BLOCK + "\n"


def main() -> int:
    required = [MAIN, INDEX, STYLE, MODULE_SRC, TEST_SRC]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        print("ERROR: AIR-1.5D prerequisite/payload missing:")
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
        ROOT / "dev-snapshots" / f"air1_5d_before_apply_{stamp}"
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
        or GEOS_CALL not in verify_main
        or GEOS_ROOT not in verify_index
        or STYLE_MARKER not in verify_style
    ):
        print("ERROR: AIR-1.5D verification failed.")
        return 4

    tropomi_pos = verify_index.find(TROPOMI_ROOT)
    geos_pos = verify_index.find(GEOS_ROOT)
    drift_pos = verify_index.find(DRIFT_ANCHOR)
    if not tropomi_pos < geos_pos < drift_pos:
        print("ERROR: AIR-1.5D DOM order verification failed.")
        return 5

    shutil.rmtree(PAYLOAD)

    print("AIR-1.5D GEOS-CF + Cross-Check Web GIS v0.1 installed.")
    print("REAL frontend mutation: APPLIED")
    print("New Web GIS layer: NASA GEOS-CF v2")
    print("Products exposed in UI: PM2.5, PM10")
    print("Default GEOS-CF field: latest run, time_index=0, stride=1")
    print("Shows: MIN/MEAN/MAX, run time, valid time, run age, opacity, click value")
    print("New operator panel: CAMS <-> GEOS-CF model cross-check")
    print("Cross-check shows: time gap, coverage, means, bias, MAE, RMSE, Pearson r")
    print("Agreement classification remains NOT CALIBRATED")
    print("Neither model is presented as ground truth")
    print("DOM order:")
    print("  CAMS")
    print("  TROPOMI")
    print("  GEOS-CF + model cross-check")
    print("  Drift Forecast")
    print("Added:")
    print("  frontend\\src\\geosCfOperationalField.js")
    print("  frontend\\src\\geosCfOperationalField.test.js")
    print("Modified:")
    print("  frontend\\index.html")
    print("  frontend\\src\\main.js")
    print("  frontend\\src\\style.css")
    print("Backup:")
    print(backup_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
