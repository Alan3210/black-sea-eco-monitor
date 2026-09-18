from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET = REPO_ROOT / "backend" / "api" / "satellite_observations.py"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

OLD_COLLECTION_BLOCK = """@router.get("/")
def get_satellite_observations(
    store: EventStore = Depends(
        get_satellite_observation_store
    ),
):
    return store.list_satellite_observations()


"""

NEW_API_BLOCK = '\ndef _matches_satellite_filters(\n    observation,\n    *,\n    observation_type=None,\n    derivation_level=None,\n    source_image_id=None,\n):\n    if (\n        observation_type is not None\n        and observation.get("observation_type")\n        != observation_type\n    ):\n        return False\n\n    if (\n        derivation_level is not None\n        and observation.get("derivation_level")\n        != derivation_level\n    ):\n        return False\n\n    if (\n        source_image_id is not None\n        and observation.get("source_image_id")\n        != source_image_id\n    ):\n        return False\n\n    return True\n\n\n@router.get("/")\ndef get_satellite_observations(\n    observation_type: str | None = None,\n    derivation_level: str | None = None,\n    source_image_id: str | None = None,\n    store: EventStore = Depends(\n        get_satellite_observation_store\n    ),\n):\n    observations = store.list_satellite_observations()\n\n    return [\n        observation\n        for observation in observations\n        if _matches_satellite_filters(\n            observation,\n            observation_type=observation_type,\n            derivation_level=derivation_level,\n            source_image_id=source_image_id,\n        )\n    ]\n\n\n@router.get("/candidates.geojson")\ndef get_satellite_candidate_geojson(\n    source_image_id: str | None = None,\n    store: EventStore = Depends(\n        get_satellite_observation_store\n    ),\n):\n    observations = store.list_satellite_observations()\n    features = []\n\n    for observation in observations:\n        if observation.get(\n            "observation_type"\n        ) != "sar_dark_spot_candidate":\n            continue\n\n        if observation.get(\n            "derivation_level"\n        ) != "derived":\n            continue\n\n        if (\n            source_image_id is not None\n            and observation.get("source_image_id")\n            != source_image_id\n        ):\n            continue\n\n        geometry = observation.get("geometry")\n\n        if not isinstance(geometry, dict):\n            continue\n\n        provenance = observation.get(\n            "provenance"\n        ) or {}\n\n        features.append(\n            {\n                "type": "Feature",\n                "id": observation.get("id"),\n                "geometry": geometry,\n                "properties": {\n                    "observation_id": observation.get(\n                        "id"\n                    ),\n                    "information_type": observation.get(\n                        "information_type"\n                    ),\n                    "derivation_level": observation.get(\n                        "derivation_level"\n                    ),\n                    "observation_type": observation.get(\n                        "observation_type"\n                    ),\n                    "source_image_id": observation.get(\n                        "source_image_id"\n                    ),\n                    "acquisition_time": observation.get(\n                        "acquisition_time"\n                    ),\n                    "review_status": observation.get(\n                        "review_status"\n                    ),\n                    "confidence": observation.get(\n                        "confidence"\n                    ),\n                    "processing_version": observation.get(\n                        "processing_version"\n                    ),\n                    "candidate_id": provenance.get(\n                        "candidate_id"\n                    ),\n                    "area_km2": provenance.get(\n                        "area_km2"\n                    ),\n                    "mean_vv_db": provenance.get(\n                        "mean_vv_db"\n                    ),\n                    "threshold_db": provenance.get(\n                        "threshold_db"\n                    ),\n                },\n            }\n        )\n\n    return {\n        "type": "FeatureCollection",\n        "features": features,\n        "semantics": {\n            "information_type": "satellite_observation",\n            "observation_type": "sar_dark_spot_candidate",\n            "does_not_mean": [\n                "oil_spill",\n                "confirmed_pollution",\n                "confirmed_event",\n                "causal_link_to_event",\n            ],\n        },\n    }\n\n\n'

DETAIL_MARKER = '@router.get("/{observation_id}")\n'


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: target not found: {TARGET}")
        return 2

    text = TARGET.read_text(encoding="utf-8")

    already_installed = (
        "def _matches_satellite_filters(" in text
        and '@router.get("/candidates.geojson")' in text
    )

    if already_installed:
        print(
            "Satellite MVP final API already installed; "
            "no edit applied."
        )
        return 0

    if OLD_COLLECTION_BLOCK not in text:
        print(
            "ERROR: expected collection endpoint block not found. "
            "No changes were made."
        )
        return 3

    if DETAIL_MARKER not in text:
        print(
            "ERROR: detail route marker not found. "
            "No changes were made."
        )
        return 4

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = (
        BACKUP_DIR
        / f"satellite_observations.before_mvp_final_{stamp}.py"
    )
    shutil.copy2(
        TARGET,
        backup,
    )

    updated = text.replace(
        OLD_COLLECTION_BLOCK,
        NEW_API_BLOCK,
        1,
    )

    TARGET.write_text(
        updated,
        encoding="utf-8",
    )

    print("Satellite MVP final API installed.")
    print(
        "Modified: backend\\api\\satellite_observations.py"
    )
    print(
        "Backup: "
        f"{backup.relative_to(REPO_ROOT)}"
    )
    print(
        "Added: collection filters + candidates.geojson endpoint."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
