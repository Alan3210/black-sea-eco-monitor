from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

PROBE = REPO_ROOT / "validation" / "gee_sentinel1_probe.json"
CALIBRATION = (
    REPO_ROOT
    / "validation"
    / "gee_sentinel1_vv_calibration_v01.json"
)
CANDIDATES = (
    REPO_ROOT
    / "validation"
    / "gee_sentinel1_dark_spot_candidates_v01.json"
)
VERIFICATION_JSON = (
    REPO_ROOT
    / "validation"
    / "sat7c_dark_spot_verification_v01.json"
)
VERIFICATION_HTML = (
    REPO_ROOT
    / "validation"
    / "sat7c_dark_spot_verification_v01.html"
)
MANIFEST = (
    REPO_ROOT
    / "validation"
    / "satellite_mvp_demo_manifest_v01.json"
)
DEFAULT_DB = REPO_ROOT / "database" / "events.db"


class DemoRunnerError(RuntimeError):
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the EkoKontur Satellite MVP demo pipeline. "
            "Use cached mode for reliable conference/demo playback "
            "or live mode to query Earth Engine."
        )
    )

    parser.add_argument(
        "--mode",
        choices=("cached", "live"),
        default="cached",
    )
    parser.add_argument(
        "--project",
        default=os.getenv("GEE_PROJECT_ID"),
    )
    parser.add_argument(
        "--authenticate",
        action="store_true",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
    )
    parser.add_argument(
        "--skip-store",
        action="store_true",
        help=(
            "Run the demo without writing candidate observations "
            "to EventStore."
        ),
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not back up the EventStore database before import.",
    )

    return parser


def required_cached_files() -> list[Path]:
    return [
        PROBE,
        CALIBRATION,
        CANDIDATES,
    ]


def validate_cached_inputs(
    paths: list[Path] | None = None,
) -> None:
    missing = [
        path
        for path in (
            paths
            if paths is not None
            else required_cached_files()
        )
        if not path.exists()
    ]

    if missing:
        joined = ", ".join(
            str(path)
            for path in missing
        )
        raise DemoRunnerError(
            f"cached demo input missing: {joined}"
        )


def python_command(
    script: Path,
    *args: str,
) -> list[str]:
    return [
        sys.executable,
        str(script),
        *args,
    ]


def _project_args(
    *,
    project: str | None,
    authenticate: bool,
) -> list[str]:
    args: list[str] = []

    if project:
        args.extend(
            [
                "--project",
                project,
            ]
        )

    if authenticate:
        args.append(
            "--authenticate"
        )

    return args


def build_live_stages(
    *,
    project: str | None,
    authenticate: bool,
    db_path: Path,
    skip_store: bool,
) -> list[dict[str, Any]]:
    ee_args = _project_args(
        project=project,
        authenticate=authenticate,
    )

    stages = [
        {
            "name": "probe",
            "mode": "live",
            "command": python_command(
                REPO_ROOT / "tools" / "gee_access_probe.py",
                *ee_args,
                "--output",
                str(PROBE),
            ),
        },
        {
            "name": "calibration",
            "mode": "live",
            "command": python_command(
                REPO_ROOT
                / "tools"
                / "gee_sentinel1_vv_calibration_v01.py",
                *ee_args,
                "--probe",
                str(PROBE),
                "--output",
                str(CALIBRATION),
            ),
        },
        {
            "name": "extraction",
            "mode": "live",
            "command": python_command(
                REPO_ROOT
                / "tools"
                / "gee_sentinel1_dark_spot_candidates_v01.py",
                *ee_args,
                "--probe",
                str(PROBE),
                "--calibration",
                str(CALIBRATION),
                "--output",
                str(CANDIDATES),
            ),
        },
        {
            "name": "verification",
            "mode": "local",
            "command": python_command(
                REPO_ROOT
                / "tools"
                / "build_sat7c_verification_map_v01.py",
                "--input",
                str(CANDIDATES),
                "--events-db",
                str(db_path),
                "--html-output",
                str(VERIFICATION_HTML),
                "--summary-output",
                str(VERIFICATION_JSON),
            ),
        },
    ]

    if not skip_store:
        stages.append(
            {
                "name": "store",
                "mode": "local",
                "command": python_command(
                    REPO_ROOT
                    / "tools"
                    / "import_sar_dark_spot_candidates_v01.py",
                    "--input",
                    str(CANDIDATES),
                    "--db",
                    str(db_path),
                ),
            }
        )

    return stages


def build_cached_stages(
    *,
    db_path: Path,
    skip_store: bool,
) -> list[dict[str, Any]]:
    stages = [
        {
            "name": "probe",
            "mode": "cached",
            "artifact": str(PROBE),
        },
        {
            "name": "calibration",
            "mode": "cached",
            "artifact": str(CALIBRATION),
        },
        {
            "name": "extraction",
            "mode": "cached",
            "artifact": str(CANDIDATES),
        },
        {
            "name": "verification",
            "mode": "local",
            "command": python_command(
                REPO_ROOT
                / "tools"
                / "build_sat7c_verification_map_v01.py",
                "--input",
                str(CANDIDATES),
                "--events-db",
                str(db_path),
                "--html-output",
                str(VERIFICATION_HTML),
                "--summary-output",
                str(VERIFICATION_JSON),
            ),
        },
    ]

    if not skip_store:
        stages.append(
            {
                "name": "store",
                "mode": "local",
                "command": python_command(
                    REPO_ROOT
                    / "tools"
                    / "import_sar_dark_spot_candidates_v01.py",
                    "--input",
                    str(CANDIDATES),
                    "--db",
                    str(db_path),
                ),
            }
        )

    return stages


def backup_database(
    db_path: Path,
) -> Path | None:
    if not db_path.exists():
        return None

    backup_dir = (
        REPO_ROOT
        / "dev-snapshots"
    )
    backup_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    stamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )
    backup = (
        backup_dir
        / f"events.before_satellite_mvp_demo_{stamp}.db"
    )

    shutil.copy2(
        db_path,
        backup,
    )

    return backup


def run_stage(
    stage: dict[str, Any],
) -> dict[str, Any]:
    if stage.get("mode") == "cached":
        artifact = Path(
            stage[
                "artifact"
            ]
        )

        if not artifact.exists():
            raise DemoRunnerError(
                f"cached stage artifact missing: {artifact}"
            )

        print(
            f"[cached] {stage['name']}: {artifact}"
        )

        return {
            "name": stage["name"],
            "mode": "cached",
            "status": "ok",
            "artifact": str(artifact),
        }

    command = stage.get(
        "command"
    )

    if not isinstance(
        command,
        list,
    ):
        raise DemoRunnerError(
            f"stage has no command: {stage['name']}"
        )

    print(
        f"[run] {stage['name']}"
    )

    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    if completed.stdout:
        print(
            completed.stdout.rstrip()
        )

    if completed.returncode != 0:
        if completed.stderr:
            print(
                completed.stderr.rstrip(),
                file=sys.stderr,
            )

        raise DemoRunnerError(
            f"stage failed: {stage['name']} "
            f"(exit {completed.returncode})"
        )

    return {
        "name": stage["name"],
        "mode": stage.get("mode"),
        "status": "ok",
        "command": command,
    }


def write_manifest(
    *,
    mode: str,
    db_path: Path,
    results: list[dict[str, Any]],
    backup_path: Path | None,
) -> None:
    MANIFEST.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "demo_version": "0.1",
        "mode": mode,
        "generated_at": utc_now_iso(),
        "database": str(db_path),
        "database_backup": (
            str(backup_path)
            if backup_path is not None
            else None
        ),
        "stages": results,
        "outputs": {
            "probe": str(PROBE),
            "calibration": str(CALIBRATION),
            "candidates": str(CANDIDATES),
            "verification_json": str(
                VERIFICATION_JSON
            ),
            "verification_html": str(
                VERIFICATION_HTML
            ),
        },
        "semantics": {
            "dark_spot_candidates_are_not": [
                "oil_spill",
                "confirmed_pollution",
                "confirmed_event",
            ]
        },
    }

    MANIFEST.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    args = build_parser().parse_args()

    db_path = args.db.resolve()

    if args.mode == "live" and not args.project:
        print(
            "ERROR: live mode requires --project "
            "or GEE_PROJECT_ID."
        )
        return 2

    try:
        if args.mode == "cached":
            validate_cached_inputs()

        backup_path = None

        if (
            not args.skip_store
            and not args.no_backup
        ):
            backup_path = backup_database(
                db_path
            )

            if backup_path is not None:
                print(
                    f"Database backup: {backup_path}"
                )

        stages = (
            build_live_stages(
                project=args.project,
                authenticate=args.authenticate,
                db_path=db_path,
                skip_store=args.skip_store,
            )
            if args.mode == "live"
            else build_cached_stages(
                db_path=db_path,
                skip_store=args.skip_store,
            )
        )

        results = [
            run_stage(
                stage
            )
            for stage in stages
        ]

        write_manifest(
            mode=args.mode,
            db_path=db_path,
            results=results,
            backup_path=backup_path,
        )

    except DemoRunnerError as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        return 3

    print()
    print("Satellite MVP demo pipeline: OK")
    print(
        f"Mode: {args.mode}"
    )
    print(
        f"Manifest: {MANIFEST}"
    )
    print(
        f"Verification map: {VERIFICATION_HTML}"
    )
    print(
        "Semantic guard: SAR dark spots are candidates only, "
        "not confirmed pollution."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
