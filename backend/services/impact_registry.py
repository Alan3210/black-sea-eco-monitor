from __future__ import annotations
import json
from pathlib import Path
from backend.schemas.impact import ImpactTarget, ImpactPosition

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "data" / "impact_registry_black_sea_v01.json"

def get_impact_registry_targets():
    records = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return [
        ImpactTarget(
            id=r["id"],
            name=r["name"],
            type=r["type"],
            position=ImpactPosition(**r["position"]),
            location_confidence=1.0,
            coordinate_source=r["source"],
        )
        for r in records
    ]
