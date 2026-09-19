from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

IMPACT_TEST = TESTS_DIR / "test_impact_api.py"
REGISTRY_TEST = TESTS_DIR / "test_impact_registry_api.py"

IMPACT_TEST_CONTENT = 'from fastapi import FastAPI\nfrom fastapi.testclient import TestClient\n\nfrom backend.api.impact import router\n\n\napp = FastAPI()\napp.include_router(router)\n\nclient = TestClient(app)\n\n\ndef test_impact_targets_endpoint_uses_registry():\n    response = client.get("/impact/targets")\n\n    assert response.status_code == 200\n\n    data = response.json()\n\n    assert len(data) == 25\n\n    names = {\n        item["name"]\n        for item in data\n    }\n\n    assert "Novorossiysk" in names\n    assert "Novorossiysk Port" in names\n    assert "Utrish Reserve" in names\n    assert "Anapa Coastal Zone" in names\n\n    types = {\n        item["type"]\n        for item in data\n    }\n\n    assert {\n        "settlement",\n        "port",\n        "protected_area",\n        "coastal_zone",\n    }.issubset(types)\n\n    assert all(\n        item["coordinate_source"]\n        == "impact_registry_v01"\n        for item in data\n    )\n\n\ndef test_impact_drift_endpoint_uses_registry_targets():\n    response = client.post(\n        "/impact/drift",\n        json={\n            "proximity_threshold_km": 1.0,\n            "forecast": {\n                "model": "OpenDrift OceanDrift",\n                "scope": (\n                    "passive_surface_tracer_current_only"\n                ),\n                "horizons": [\n                    {\n                        "hours": 6,\n                        "time": (\n                            "2026-09-17T06:00:00+00:00"\n                        ),\n                        "points": [\n                            [37.769, 44.724]\n                        ],\n                    }\n                ],\n            },\n        },\n    )\n\n    assert response.status_code == 200\n\n    data = response.json()\n\n    assert (\n        data["analysis_type"]\n        == "drift_proximity_screening_v0.1"\n    )\n\n    assert data["target_count"] == 25\n    assert data["potentially_affected_count"] >= 1\n\n    novorossiysk = next(\n        item\n        for item in data["assessments"]\n        if item["target"]["name"] == "Novorossiysk"\n    )\n\n    assert novorossiysk["potentially_affected"] is True\n    assert novorossiysk["first_exposure_hours"] == 6\n    assert novorossiysk["minimum_distance_km"] == 0.0\n'
REGISTRY_TEST_CONTENT = 'from fastapi import FastAPI\nfrom fastapi.testclient import TestClient\n\nfrom backend.api.impact_registry import router\n\n\napp = FastAPI()\napp.include_router(router)\n\nclient = TestClient(app)\n\n\ndef test_impact_registry_endpoint():\n    response = client.get("/impact/registry")\n\n    assert response.status_code == 200\n\n    data = response.json()\n\n    assert data["registry"] == "impact_registry_v01"\n    assert data["count"] == 25\n    assert len(data["targets"]) == 25\n\n    names = {\n        item["name"]\n        for item in data["targets"]\n    }\n\n    assert "Novorossiysk Port" in names\n    assert "Utrish Reserve" in names\n'


def backup(path: Path, label: str) -> Path | None:
    if not path.exists():
        return None

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = (
        BACKUP_DIR
        / f"{label}.before_system5_test_contract_{stamp}{path.suffix}"
    )
    shutil.copy2(path, target)
    return target


def main() -> int:
    impact_api = REPO_ROOT / "backend" / "api" / "impact.py"
    registry_api = (
        REPO_ROOT / "backend" / "api" / "impact_registry.py"
    )
    registry_service = (
        REPO_ROOT
        / "backend"
        / "services"
        / "impact_registry.py"
    )

    for path in [
        impact_api,
        registry_api,
        registry_service,
    ]:
        if not path.exists():
            print(f"ERROR: required SYSTEM-5 file missing: {path}")
            return 2

    backups = []

    for path, label in [
        (IMPACT_TEST, "test_impact_api"),
        (REGISTRY_TEST, "test_impact_registry_api"),
    ]:
        saved = backup(path, label)
        if saved is not None:
            backups.append(saved)

    TESTS_DIR.mkdir(parents=True, exist_ok=True)

    IMPACT_TEST.write_text(
        IMPACT_TEST_CONTENT,
        encoding="utf-8",
    )
    REGISTRY_TEST.write_text(
        REGISTRY_TEST_CONTENT,
        encoding="utf-8",
    )

    print("SYSTEM-5 test contract patch installed.")
    print("Updated:")
    print("  tests/test_impact_api.py")
    print("Added/updated:")
    print("  tests/test_impact_registry_api.py")
    print("Contract:")
    print("  /impact/targets -> 25 registry targets")
    print("  /impact/drift -> registry-backed target_count")
    print("  /impact/registry -> registry metadata/count")

    if backups:
        print("Backups:")
        for item in backups:
            print(f"  {item.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
