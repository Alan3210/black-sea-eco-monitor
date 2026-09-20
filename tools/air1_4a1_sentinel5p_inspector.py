from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

import numpy as np

try:
    import rasterio
except ImportError as exc:
    raise SystemExit(
        "rasterio is required for AIR-1.4A.1 inspection. "
        "Install it in the project venv with: pip install rasterio"
    ) from exc


def _finite_stats(values: np.ndarray) -> dict:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "p05": None,
            "p25": None,
            "p50": None,
            "p75": None,
            "p95": None,
        }

    percentiles = np.percentile(
        finite.astype(np.float64, copy=False),
        [5, 25, 50, 75, 95],
    )
    return {
        "count": int(finite.size),
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "mean": float(np.mean(finite)),
        "p05": float(percentiles[0]),
        "p25": float(percentiles[1]),
        "p50": float(percentiles[2]),
        "p75": float(percentiles[3]),
        "p95": float(percentiles[4]),
    }


def inspect_geotiff(path: Path) -> dict:
    with rasterio.open(path) as ds:
        bands = ds.read(masked=False)

        report = {
            "status": "ok",
            "path": str(path),
            "driver": ds.driver,
            "width": int(ds.width),
            "height": int(ds.height),
            "count": int(ds.count),
            "dtypes": list(ds.dtypes),
            "crs": str(ds.crs) if ds.crs else None,
            "bounds": {
                "left": float(ds.bounds.left),
                "bottom": float(ds.bounds.bottom),
                "right": float(ds.bounds.right),
                "top": float(ds.bounds.top),
            },
            "transform": list(ds.transform)[:6],
            "nodata": ds.nodata,
            "descriptions": list(ds.descriptions),
            "colorinterp": [str(x) for x in ds.colorinterp],
            "tags": ds.tags(),
            "bands": [],
        }

        for idx in range(ds.count):
            arr = bands[idx].astype(np.float64, copy=False)
            finite = np.isfinite(arr)
            zero_count = int(np.count_nonzero(finite & (arr == 0)))
            nan_count = int(arr.size - np.count_nonzero(finite))
            report["bands"].append(
                {
                    "index": idx + 1,
                    "dtype": ds.dtypes[idx],
                    "shape": [int(arr.shape[0]), int(arr.shape[1])],
                    "zero_count": zero_count,
                    "nan_count": nan_count,
                    "all_finite_stats": _finite_stats(arr),
                }
            )

        if ds.count >= 2:
            value = bands[0].astype(np.float64, copy=False)
            data_mask = bands[1].astype(np.float64, copy=False)

            valid = (
                np.isfinite(value)
                & np.isfinite(data_mask)
                & (data_mask > 0)
            )

            masked_values = value[valid]
            valid_count = int(np.count_nonzero(valid))
            total_count = int(valid.size)

            report["scientific_value_band"] = {
                "band_index": 1,
                "valid_by_dataMask_stats": _finite_stats(masked_values),
                "valid_pixel_count": valid_count,
                "total_pixel_count": total_count,
                "valid_fraction": (
                    float(valid_count / total_count)
                    if total_count
                    else 0.0
                ),
                "valid_percent": (
                    float(100.0 * valid_count / total_count)
                    if total_count
                    else 0.0
                ),
            }

            mask_finite = data_mask[np.isfinite(data_mask)]
            unique = np.unique(mask_finite)
            if unique.size <= 20:
                unique_values = [float(x) for x in unique.tolist()]
            else:
                unique_values = [
                    float(np.min(mask_finite)),
                    float(np.max(mask_finite)),
                ]

            report["dataMask_band"] = {
                "band_index": 2,
                "unique_values": unique_values,
                "positive_pixel_count": int(
                    np.count_nonzero(
                        np.isfinite(data_mask) & (data_mask > 0)
                    )
                ),
                "zero_pixel_count": int(
                    np.count_nonzero(
                        np.isfinite(data_mask) & (data_mask == 0)
                    )
                ),
            }

        report["inspected_at"] = (
            datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        )
        return report


def find_latest(root: Path, product: str) -> Path:
    product_dir = root / product
    candidates = sorted(
        product_dir.glob("*.tif"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(
            f"No cached GeoTIFF found in {product_dir}"
        )
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect cached Sentinel-5P/TROPOMI GeoTIFF."
    )
    parser.add_argument(
        "--path",
        type=Path,
        help="Specific GeoTIFF path. If omitted, latest cached file is used.",
    )
    parser.add_argument(
        "--product",
        default="no2",
        help="Cache product folder used when --path is omitted.",
    )
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=Path("data/cache/air/sentinel5p"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "validation/air1_4a1_sentinel5p_geotiff_inspection.json"
        ),
    )
    args = parser.parse_args()

    try:
        path = (
            args.path
            if args.path is not None
            else find_latest(args.cache_root, args.product)
        )
        if not path.exists():
            raise FileNotFoundError(str(path))

        report = inspect_geotiff(path)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print()
    print(f"Saved: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
