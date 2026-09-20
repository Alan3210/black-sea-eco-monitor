from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.services.cams_netcdf_inspection import (
    inspect_netcdf,
    write_inspection_json,
)


DEFAULT_CACHE = Path(
    "data/cache/air/cams-europe"
)

DEFAULT_OUTPUT = Path(
    "validation/air1_3a1_cams_netcdf_inspection.json"
)


def newest_cams_netcdf(
    cache_root: Path = DEFAULT_CACHE,
) -> Path:
    files = list(
        cache_root.rglob(
            "ENS_FORECAST.nc"
        )
    )

    if not files:
        files = list(
            cache_root.rglob(
                "*.nc"
            )
        )

    if not files:
        raise FileNotFoundError(
            "No CAMS NetCDF files found under "
            f"{cache_root}"
        )

    return max(
        files,
        key=lambda path:
            path.stat().st_mtime,
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the newest real CAMS Europe "
            "NetCDF artifact downloaded by AIR-1.3A."
        )
    )

    parser.add_argument(
        "--path",
        default=None,
        help=(
            "Optional explicit NetCDF path. "
            "Default: newest cached CAMS *.nc."
        ),
    )

    parser.add_argument(
        "--output",
        default=str(
            DEFAULT_OUTPUT
        ),
        help=(
            "JSON inspection output path."
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    path = (
        Path(args.path)
        if args.path
        else newest_cams_netcdf()
    )

    inspection = inspect_netcdf(
        path
    )

    output = write_inspection_json(
        inspection,
        args.output,
    )

    summary = {
        "path": inspection["path"],
        "file_size_bytes":
            inspection["file_size_bytes"],
        "dims": inspection["dims"],
        "detected_axes":
            inspection["detected_axes"],
        "data_variables": {
            name: {
                "dims":
                    info["dims"],
                "shape":
                    info["shape"],
                "units":
                    info["attrs"].get(
                        "units"
                    ),
                "long_name":
                    info["attrs"].get(
                        "long_name"
                    ),
                "standard_name":
                    info["attrs"].get(
                        "standard_name"
                    ),
                "min":
                    info.get("min"),
                "max":
                    info.get("max"),
                "mean":
                    info.get("mean"),
            }
            for name, info
            in inspection[
                "data_variables"
            ].items()
        },
        "coordinates": {
            name: {
                "shape":
                    info["shape"],
                "dtype":
                    info["dtype"],
                "first":
                    info["first"],
                "last":
                    info["last"],
                "orientation":
                    info["orientation"],
                "units":
                    info["attrs"].get(
                        "units"
                    ),
            }
            for name, info
            in inspection[
                "coordinates"
            ].items()
        },
        "output": str(output),
    }

    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
