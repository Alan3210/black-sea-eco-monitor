from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import re
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = REPO_ROOT / ".weather1_5b_payload"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

TARGETS = {
    "frontend/index.html": (
        "308668eab65c0a9e1165c891717ea749dd54cb05c21c42b811fef3e420f5da28"
    ),
    "frontend/src/main.js": (
        "dd73a53c68baad080c1172c98b61ed22281b0b2e0b8774747aecdf89f3981b5d"
    ),
    "frontend/src/i18n.js": (
        "bfb07ca682b6b53abb0112fa8374e51dc807f3d9313efeeac040aa48cce99816"
    ),
    "frontend/src/style.css": (
        "90b920f8fd73b32ac0a23449b16651221ccd3f85d5129a3c67548da5f7f820a9"
    ),
}

NEW_FILES = [
    "frontend/src/wind.js",
    "frontend/src/wind.test.js",
]

VITE = REPO_ROOT / "frontend" / "vite.config.js"


def sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def patch_vite(text: str) -> str:
    normalized = text.replace(
        "\r\n",
        "\n",
    )

    if "'/weather':" in normalized:
        return text

    pattern = re.compile(
        r"(?P<indent>^[ \t]*)'/ocean':\s*\{\s*\n"
        r"(?P<body>.*?\n)"
        r"(?P=indent)\},",
        re.MULTILINE | re.DOTALL,
    )

    match = pattern.search(
        normalized
    )

    if match is None:
        raise RuntimeError(
            "frontend/vite.config.js: /ocean proxy block not found"
        )

    indent = match.group(
        "indent"
    )

    block = match.group(0)

    weather_block = (
        "\n"
        f"{indent}'/weather': {{\n"
        f"{indent}  target: 'http://127.0.0.1:8000',\n"
        f"{indent}  changeOrigin: false,\n"
        f"{indent}}},"
    )

    patched = normalized.replace(
        block,
        block + weather_block,
        1,
    )

    newline = (
        "\r\n"
        if "\r\n" in text
        else "\n"
    )

    return patched.replace(
        "\n",
        newline,
    )


def cleanup_payload() -> None:
    if PAYLOAD_ROOT.exists():
        shutil.rmtree(
            PAYLOAD_ROOT,
        )


def main() -> int:
    marker_file = (
        REPO_ROOT
        / "frontend"
        / "src"
        / "main.js"
    )

    if (
        marker_file.exists()
        and "WEATHER-1.5B" in marker_file.read_text(
            encoding="utf-8",
            errors="replace",
        )
    ):
        cleanup_payload()
        print(
            "WEATHER-1.5B Web GIS wind arrows already installed."
        )
        return 0

    missing = []

    for rel in TARGETS:
        path = REPO_ROOT / rel

        if not path.exists():
            missing.append(
                rel
            )

    for rel in NEW_FILES:
        path = REPO_ROOT / rel

        if not path.exists():
            missing.append(
                rel
            )

    if not VITE.exists():
        missing.append(
            "frontend/vite.config.js"
        )

    for rel in TARGETS:
        payload = (
            PAYLOAD_ROOT
            / rel
        )

        if not payload.exists():
            missing.append(
                f".weather1_5b_payload/{rel}"
            )

    if missing:
        print(
            "ERROR: package/repository files are missing:"
        )
        for rel in missing:
            print(
                f"  {rel}"
            )
        return 2

    mismatches = []

    for rel, expected in TARGETS.items():
        path = REPO_ROOT / rel
        actual = sha256(
            path
        )

        if actual != expected:
            mismatches.append(
                (
                    rel,
                    expected,
                    actual,
                )
            )

    if mismatches:
        print(
            "ERROR: frontend source does not match the clean WEATHER-1.4 baseline used to build this package."
        )
        print(
            "No tracked frontend files were modified."
        )

        for (
            rel,
            expected,
            actual,
        ) in mismatches:
            print(
                f"  {rel}"
            )
            print(
                f"    expected: {expected}"
            )
            print(
                f"    actual:   {actual}"
            )

        return 3

    try:
        vite_original = VITE.read_text(
            encoding="utf-8",
        )
        vite_patched = patch_vite(
            vite_original
        )
    except RuntimeError as exc:
        print(
            f"ERROR: {exc}"
        )
        print(
            "No tracked frontend files were modified."
        )
        return 4

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    backup_map = {}

    for rel in [
        *TARGETS.keys(),
        "frontend/vite.config.js",
    ]:
        source = REPO_ROOT / rel
        safe_name = (
            rel
            .replace("/", "_")
            .replace("\\", "_")
        )
        backup = (
            BACKUP_DIR
            / (
                f"{safe_name}"
                f".before_weather1_5b_"
                f"{stamp}"
            )
        )
        shutil.copy2(
            source,
            backup,
        )
        backup_map[
            rel
        ] = backup

    try:
        for rel in TARGETS:
            shutil.copy2(
                PAYLOAD_ROOT
                / rel,
                REPO_ROOT
                / rel,
            )

        if vite_patched != vite_original:
            VITE.write_text(
                vite_patched,
                encoding="utf-8",
                newline="",
            )
    except Exception:
        for rel, backup in backup_map.items():
            shutil.copy2(
                backup,
                REPO_ROOT / rel,
            )
        raise

    cleanup_payload()

    print(
        "WEATHER-1.5B Web GIS Wind Arrows v0.1 installed."
    )
    print(
        "Modified:"
    )
    print(
        "  frontend/index.html"
    )
    print(
        "  frontend/src/main.js"
    )
    print(
        "  frontend/src/i18n.js"
    )
    print(
        "  frontend/src/style.css"
    )
    print(
        "  frontend/vite.config.js"
    )
    print(
        "Added:"
    )
    print(
        "  frontend/src/wind.js"
    )
    print(
        "  frontend/src/wind.test.js"
    )
    print(
        "Wind API:"
    )
    print(
        "  GET /weather/wind-field"
    )
    print(
        "Scientific direction semantics:"
    )
    print(
        "  popup FROM = meteorological direction"
    )
    print(
        "  map arrow = physical TO direction"
    )
    print(
        "No backend, OceanDrift, current-layer, or impact physics were modified."
    )
    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
