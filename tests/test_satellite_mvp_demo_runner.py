from pathlib import Path

import pytest

from tools.run_satellite_mvp_demo_v01 import (
    DemoRunnerError,
    build_cached_stages,
    build_live_stages,
    validate_cached_inputs,
)


def test_cached_plan_preserves_pipeline_order():
    stages = build_cached_stages(
        db_path=Path("database/events.db"),
        skip_store=False,
    )

    assert [
        stage["name"]
        for stage in stages
    ] == [
        "probe",
        "calibration",
        "extraction",
        "verification",
        "store",
    ]

    assert [
        stage["mode"]
        for stage in stages[:3]
    ] == [
        "cached",
        "cached",
        "cached",
    ]


def test_cached_plan_can_skip_store():
    stages = build_cached_stages(
        db_path=Path("database/events.db"),
        skip_store=True,
    )

    assert [
        stage["name"]
        for stage in stages
    ] == [
        "probe",
        "calibration",
        "extraction",
        "verification",
    ]


def test_live_plan_preserves_pipeline_order():
    stages = build_live_stages(
        project="test-project",
        authenticate=False,
        db_path=Path("database/events.db"),
        skip_store=False,
    )

    assert [
        stage["name"]
        for stage in stages
    ] == [
        "probe",
        "calibration",
        "extraction",
        "verification",
        "store",
    ]

    assert stages[0]["mode"] == "live"
    assert "--project" in stages[0]["command"]
    assert "test-project" in stages[0]["command"]


def test_live_plan_propagates_authentication():
    stages = build_live_stages(
        project="test-project",
        authenticate=True,
        db_path=Path("database/events.db"),
        skip_store=True,
    )

    for stage in stages[:3]:
        assert "--authenticate" in stage[
            "command"
        ]


def test_validate_cached_inputs_accepts_existing_files(
    tmp_path,
):
    paths = []

    for name in (
        "probe.json",
        "calibration.json",
        "candidates.json",
    ):
        path = tmp_path / name
        path.write_text(
            "{}",
            encoding="utf-8",
        )
        paths.append(path)

    validate_cached_inputs(
        paths
    )


def test_validate_cached_inputs_rejects_missing_file(
    tmp_path,
):
    existing = tmp_path / "probe.json"
    existing.write_text(
        "{}",
        encoding="utf-8",
    )

    missing = tmp_path / "missing.json"

    with pytest.raises(
        DemoRunnerError,
        match="cached demo input missing",
    ):
        validate_cached_inputs(
            [
                existing,
                missing,
            ]
        )
