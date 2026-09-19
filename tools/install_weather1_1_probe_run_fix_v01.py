from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "tools" / "weather1_1_ecmwf_point_probe.py"
WEATHER_INSTALLER = (
    REPO_ROOT
    / "tools"
    / "install_weather1_1_ecmwf_provider_v01.py"
)
README = REPO_ROOT / "README_WEATHER1_1_ECMWF_PROVIDER_V01.txt"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

OLD_PROBE_IMPORT = """from __future__ import annotations

import argparse
import json

from backend.services.ecmwf_weather_provider import (
"""

NEW_PROBE_IMPORT = """from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Allow both:
#   python -m tools.weather1_1_ecmwf_point_probe
# and:
#   python .\\tools\\weather1_1_ecmwf_point_probe.py
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.ecmwf_weather_provider import (
"""


def backup(path: Path, label: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = (
        BACKUP_DIR
        / f"{label}.before_weather1_1_probe_fix_{stamp}{path.suffix}"
    )
    shutil.copy2(path, target)
    return target


def patch_probe(text: str) -> str:
    if "REPO_ROOT = Path(__file__).resolve().parents[1]" in text:
        return text
    if OLD_PROBE_IMPORT not in text:
        raise RuntimeError("probe import marker not found")
    return text.replace(
        OLD_PROBE_IMPORT,
        NEW_PROBE_IMPORT,
        1,
    )


def patch_weather_installer(text: str) -> str:
    # The WEATHER-1.1 installer embeds the probe source in its FILES dict.
    # Replace the original embedded source fragment so reinstalling WEATHER-1.1
    # will not reintroduce the direct-run import bug.
    if "Allow both:" in text:
        return text

    old = OLD_PROBE_IMPORT.replace("\\", "\\\\")
    # repr() encoding used by the generated installer preserves newlines as \n.
    old_repr_fragment = (
        "from __future__ import annotations\\n\\n"
        "import argparse\\n"
        "import json\\n\\n"
        "from backend.services.ecmwf_weather_provider import (\\n"
    )
    new_repr_fragment = (
        "from __future__ import annotations\\n\\n"
        "import argparse\\n"
        "import json\\n"
        "from pathlib import Path\\n"
        "import sys\\n\\n"
        "# Allow both:\\n"
        "#   python -m tools.weather1_1_ecmwf_point_probe\\n"
        "# and:\\n"
        "#   python .\\\\tools\\\\weather1_1_ecmwf_point_probe.py\\n"
        "REPO_ROOT = Path(__file__).resolve().parents[1]\\n"
        "if str(REPO_ROOT) not in sys.path:\\n"
        "    sys.path.insert(0, str(REPO_ROOT))\\n\\n"
        "from backend.services.ecmwf_weather_provider import (\\n"
    )

    if old_repr_fragment not in text:
        raise RuntimeError("embedded probe source marker not found")

    return text.replace(
        old_repr_fragment,
        new_repr_fragment,
        1,
    )


def patch_readme(text: str) -> str:
    note = (
        "\nProbe launch note\n"
        "-----------------\n"
        "The probe supports both direct execution and module execution:\n"
        "python .\\tools\\weather1_1_ecmwf_point_probe.py --lat 44.60 --lon 37.80\n"
        "python -m tools.weather1_1_ecmwf_point_probe --lat 44.60 --lon 37.80\n"
    )
    if "Probe launch note" in text:
        return text
    return text.rstrip() + note + "\n"


def main() -> int:
    for path in (PROBE, WEATHER_INSTALLER, README):
        if not path.exists():
            print(f"ERROR: required WEATHER-1.1 file missing: {path}")
            return 2

    probe_text = PROBE.read_text(encoding="utf-8")
    installer_text = WEATHER_INSTALLER.read_text(encoding="utf-8")
    readme_text = README.read_text(encoding="utf-8")

    try:
        new_probe = patch_probe(probe_text)
        new_installer = patch_weather_installer(installer_text)
        new_readme = patch_readme(readme_text)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        print("No file was modified.")
        return 3

    backups = []
    for path, label in (
        (PROBE, "weather1_1_probe"),
        (WEATHER_INSTALLER, "weather1_1_installer"),
        (README, "weather1_1_readme"),
    ):
        old = path.read_text(encoding="utf-8")
        new = {
            PROBE: new_probe,
            WEATHER_INSTALLER: new_installer,
            README: new_readme,
        }[path]
        if old != new:
            backups.append(backup(path, label))
            path.write_text(new, encoding="utf-8")

    print("WEATHER-1.1 direct probe launch fix installed.")
    print("Updated:")
    print("  tools/weather1_1_ecmwf_point_probe.py")
    print("  tools/install_weather1_1_ecmwf_provider_v01.py")
    print("  README_WEATHER1_1_ECMWF_PROVIDER_V01.txt")
    print("Direct launch is now supported.")
    if backups:
        print("Backups:")
        for item in backups:
            print(f"  {item.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
