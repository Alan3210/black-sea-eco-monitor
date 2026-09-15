import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


from agents.ocean_data.copernicus_currents import (
    get_surface_currents,
)


def main():
    payload = get_surface_currents()

    vectors = payload.get("vectors") or []

    print("OCEAN DATA V1 - CURRENT CHECK")
    print(
        f"Dataset: {payload.get('dataset_id')}"
    )
    print(
        f"Valid time: {payload.get('valid_time')}"
    )
    print(
        f"Depth: {payload.get('depth_m')} m"
    )
    print(
        f"Vectors: {len(vectors)}"
    )
    print(
        f"Cache: {(payload.get('cache') or {}).get('status')}"
    )

    if vectors:
        speeds = [
            item["speed"]
            for item in vectors
        ]

        print(
            f"Speed min: {min(speeds):.4f} m/s"
        )
        print(
            f"Speed max: {max(speeds):.4f} m/s"
        )
        print(
            f"Speed avg: "
            f"{sum(speeds) / len(speeds):.4f} m/s"
        )

        print()
        print("Sample vectors:")

        for item in vectors[:5]:
            print(
                f"  {item['latitude']}, "
                f"{item['longitude']} | "
                f"u={item['u']} "
                f"v={item['v']} "
                f"speed={item['speed']} "
                f"dir={item['direction_deg']} deg"
            )


if __name__ == "__main__":
    main()
