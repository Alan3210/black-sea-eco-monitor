from __future__ import annotations

import csv
import json
import math
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from agents.ocean_data.dynamic_forcing_validation import (
    normalize_target_time,
)
from agents.ocean_data.dynamic_openoil import (
    run_dynamic_openoil,
)


MASS_BALANCE_WARNING_PERCENT = 0.1


@dataclass(frozen=True)
class ValidationScenario:
    key: str
    label: str
    longitude: float
    latitude: float
    description: str


@dataclass(frozen=True)
class ValidationCase:
    scenario: ValidationScenario
    hours: int
    particles: int
    half_width_deg: float
    release_volume_m3: float = 1.0
    radius_m: float = 200.0


DEFAULT_SCENARIOS: tuple[
    ValidationScenario,
    ...
] = (
    ValidationScenario(
        key="novorossiysk_nearshore",
        label="Novorossiysk nearshore",
        longitude=37.7691,
        latitude=44.7240,
        description=(
            "Near-shore reference case already used in OpenOil validation."
        ),
    ),
    ValidationScenario(
        key="eastern_black_sea_offshore",
        label="Eastern Black Sea offshore",
        longitude=37.0000,
        latitude=44.0000,
        description=(
            "Offshore eastern-basin case intended to reduce immediate "
            "coastline interaction."
        ),
    ),
    ValidationScenario(
        key="central_black_sea",
        label="Central Black Sea",
        longitude=34.0000,
        latitude=43.5000,
        description=(
            "Central-basin case for testing a long-lived open-water plume."
        ),
    ),
)


PROFILE_CONFIGS = {
    "smoke": {
        "hours": (6,),
        "particles": (100,),
        "half_width_deg": (1.0,),
    },
    "standard": {
        "hours": (6, 12),
        "particles": (100, 500),
        "half_width_deg": (1.0, 2.0),
    },
    "full": {
        "hours": (6, 12, 24),
        "particles": (100, 500),
        "half_width_deg": (1.0, 2.0),
    },
}


def scenario_map() -> dict[str, ValidationScenario]:
    return {
        scenario.key: scenario
        for scenario in DEFAULT_SCENARIOS
    }


def select_scenarios(
    keys: Iterable[str] | None = None,
) -> tuple[ValidationScenario, ...]:
    if not keys:
        return DEFAULT_SCENARIOS

    available = scenario_map()
    selected = []

    for key in keys:
        if key not in available:
            raise ValueError(
                f"Unknown scenario '{key}'. "
                f"Available: {', '.join(sorted(available))}"
            )
        selected.append(
            available[key]
        )

    return tuple(selected)


def build_validation_cases(
    *,
    profile: str,
    scenario_keys: Iterable[str] | None = None,
) -> list[ValidationCase]:
    if profile not in PROFILE_CONFIGS:
        raise ValueError(
            "profile must be one of: "
            + ", ".join(
                PROFILE_CONFIGS
            )
        )

    config = PROFILE_CONFIGS[
        profile
    ]
    scenarios = select_scenarios(
        scenario_keys
    )

    cases = []

    for scenario in scenarios:
        for hours in config[
            "hours"
        ]:
            for particles in config[
                "particles"
            ]:
                for half_width_deg in config[
                    "half_width_deg"
                ]:
                    cases.append(
                        ValidationCase(
                            scenario=scenario,
                            hours=int(hours),
                            particles=int(
                                particles
                            ),
                            half_width_deg=float(
                                half_width_deg
                            ),
                        )
                    )

    return cases


def haversine_km(
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
) -> float:
    earth_radius_km = 6371.0088

    lon1_r = math.radians(
        float(lon1)
    )
    lat1_r = math.radians(
        float(lat1)
    )
    lon2_r = math.radians(
        float(lon2)
    )
    lat2_r = math.radians(
        float(lat2)
    )

    delta_lon = lon2_r - lon1_r
    delta_lat = lat2_r - lat1_r

    a = (
        math.sin(
            delta_lat / 2
        ) ** 2
        + math.cos(
            lat1_r
        )
        * math.cos(
            lat2_r
        )
        * math.sin(
            delta_lon / 2
        ) ** 2
    )

    return (
        2
        * earth_radius_km
        * math.asin(
            math.sqrt(a)
        )
    )


def case_id(
    case: ValidationCase,
) -> str:
    half_width = (
        f"{case.half_width_deg:g}"
        .replace(
            ".",
            "p",
        )
    )

    return (
        f"{case.scenario.key}"
        f"_h{case.hours}"
        f"_p{case.particles}"
        f"_box{half_width}"
    )


def stranded_percent(
    payload: dict,
) -> float | None:
    runtime = payload.get(
        "runtime_state",
        {}
    )
    reasons = runtime.get(
        "deactivation_reason_counts",
        {}
    )
    seeded = runtime.get(
        "seeded_elements",
        payload.get(
            "release",
            {}
        ).get(
            "particles"
        ),
    )

    if not seeded:
        return None

    stranded = float(
        reasons.get(
            "stranded",
            0
        )
    )

    return stranded / float(
        seeded
    ) * 100.0


def evaporated_percent(
    payload: dict,
) -> float | None:
    budget = payload.get(
        "mass_budget",
        {}
    )
    initial = budget.get(
        "initial_oil_kg"
    )
    evaporated = budget.get(
        "evaporated_kg"
    )

    if (
        initial is None
        or evaporated is None
        or abs(
            float(initial)
        )
        <= 1e-12
    ):
        return None

    return (
        float(evaporated)
        / float(initial)
        * 100.0
    )


def summarize_payload(
    *,
    case: ValidationCase,
    payload: dict,
    runtime_seconds: float,
) -> dict:
    final_positions = payload.get(
        "final_positions",
        {}
    )
    center = (
        final_positions.get(
            "center"
        )
        or {}
    )
    runtime_state = payload.get(
        "runtime_state",
        {}
    )
    mass_budget = payload.get(
        "mass_budget",
        {}
    )
    seed = payload.get(
        "model_seed_location",
        {}
    )
    simulation = payload.get(
        "simulation",
        {}
    )

    row = {
        "case_id": case_id(
            case
        ),
        "scenario": (
            case.scenario.key
        ),
        "scenario_label": (
            case.scenario.label
        ),
        "requested_longitude": (
            case.scenario.longitude
        ),
        "requested_latitude": (
            case.scenario.latitude
        ),
        "hours": case.hours,
        "particles": case.particles,
        "half_width_deg": (
            case.half_width_deg
        ),
        "release_volume_m3": (
            case.release_volume_m3
        ),
        "radius_m": (
            case.radius_m
        ),
        "forecast_status": payload.get(
            "forecast_status"
        ),
        "forecast_complete": (
            payload.get(
                "forecast_complete"
            )
        ),
        "completion_reason": (
            payload.get(
                "completion_reason"
            )
        ),
        "requested_end_time": (
            simulation.get(
                "requested_end_time"
            )
        ),
        "actual_result_end_time": (
            simulation.get(
                "actual_result_end_time"
            )
        ),
        "reached_requested_end": (
            simulation.get(
                "reached_requested_end"
            )
        ),
        "seed_longitude": seed.get(
            "longitude"
        ),
        "seed_latitude": seed.get(
            "latitude"
        ),
        "seed_shift_km": seed.get(
            "distance_km"
        ),
        "final_center_longitude": (
            center.get(
                "longitude"
            )
        ),
        "final_center_latitude": (
            center.get(
                "latitude"
            )
        ),
        "trajectory_count": (
            final_positions.get(
                "trajectory_count"
            )
        ),
        "final_particle_count": (
            final_positions.get(
                "particle_count"
            )
        ),
        "active_elements": (
            runtime_state.get(
                "active_elements"
            )
        ),
        "deactivated_elements": (
            runtime_state.get(
                "deactivated_elements"
            )
        ),
        "scheduled_elements": (
            runtime_state.get(
                "scheduled_elements"
            )
        ),
        "all_elements_accounted": (
            runtime_state.get(
                "all_elements_accounted"
            )
        ),
        "physical_terminal_state": (
            runtime_state.get(
                "physical_terminal_state"
            )
        ),
        "stranded_percent": (
            stranded_percent(
                payload
            )
        ),
        "initial_oil_kg": (
            mass_budget.get(
                "initial_oil_kg"
            )
        ),
        "remaining_oil_kg": (
            mass_budget.get(
                "remaining_oil_kg"
            )
        ),
        "evaporated_kg": (
            mass_budget.get(
                "evaporated_kg"
            )
        ),
        "evaporated_percent": (
            evaporated_percent(
                payload
            )
        ),
        "dispersed_kg": (
            mass_budget.get(
                "dispersed_kg"
            )
        ),
        "accounted_mass_kg": (
            mass_budget.get(
                "accounted_mass_kg"
            )
        ),
        "mass_closure_error_percent": (
            mass_budget.get(
                "mass_closure_error_percent"
            )
        ),
        "trajectories_with_mass": (
            mass_budget.get(
                "trajectories_with_mass"
            )
        ),
        "runtime_seconds": round(
            float(
                runtime_seconds
            ),
            2,
        ),
        "error": None,
    }

    row["health_status"] = (
        classify_health(
            row
        )
    )

    return row


def classify_health(
    row: dict,
) -> str:
    if row.get(
        "error"
    ):
        return "ERROR"

    if not row.get(
        "all_elements_accounted",
        False,
    ):
        return "ACCOUNTING_WARN"

    trajectories = row.get(
        "trajectories_with_mass"
    )
    particles = row.get(
        "particles"
    )

    if (
        trajectories is not None
        and particles is not None
        and int(
            trajectories
        )
        != int(
            particles
        )
    ):
        return "MASS_ACCOUNTING_WARN"

    closure = row.get(
        "mass_closure_error_percent"
    )

    if (
        closure is not None
        and abs(
            float(
                closure
            )
        )
        > MASS_BALANCE_WARNING_PERCENT
    ):
        return "MASS_BALANCE_WARN"

    if not row.get(
        "forecast_complete",
        False,
    ):
        return "INCOMPLETE"

    if row.get(
        "physical_terminal_state"
    ):
        return "TERMINAL_COMPLETE"

    return "COMPLETE"


def error_summary(
    *,
    case: ValidationCase,
    error: Exception,
    runtime_seconds: float,
) -> dict:
    return {
        "case_id": case_id(
            case
        ),
        "scenario": (
            case.scenario.key
        ),
        "scenario_label": (
            case.scenario.label
        ),
        "requested_longitude": (
            case.scenario.longitude
        ),
        "requested_latitude": (
            case.scenario.latitude
        ),
        "hours": case.hours,
        "particles": case.particles,
        "half_width_deg": (
            case.half_width_deg
        ),
        "release_volume_m3": (
            case.release_volume_m3
        ),
        "radius_m": case.radius_m,
        "forecast_status": None,
        "forecast_complete": False,
        "completion_reason": None,
        "runtime_seconds": round(
            float(
                runtime_seconds
            ),
            2,
        ),
        "error": (
            f"{type(error).__name__}: "
            f"{error}"
        ),
        "health_status": "ERROR",
    }


def choose_reference_row(
    rows: list[dict],
) -> dict | None:
    usable = [
        row
        for row in rows
        if (
            not row.get(
                "error"
            )
            and row.get(
                "final_center_longitude"
            )
            is not None
            and row.get(
                "final_center_latitude"
            )
            is not None
        )
    ]

    if not usable:
        return None

    return max(
        usable,
        key=lambda row: (
            int(
                row.get(
                    "particles",
                    0,
                )
            ),
            float(
                row.get(
                    "half_width_deg",
                    0,
                )
            ),
        ),
    )


def add_reference_deltas(
    rows: list[dict],
) -> None:
    groups: dict[
        tuple[str, int],
        list[dict],
    ] = {}

    for row in rows:
        key = (
            str(
                row.get(
                    "scenario"
                )
            ),
            int(
                row.get(
                    "hours",
                    0,
                )
            ),
        )
        groups.setdefault(
            key,
            [],
        ).append(
            row
        )

    for group_rows in groups.values():
        reference = (
            choose_reference_row(
                group_rows
            )
        )

        for row in group_rows:
            row[
                "reference_case_id"
            ] = (
                reference.get(
                    "case_id"
                )
                if reference
                else None
            )

            row[
                "center_delta_km_to_reference"
            ] = None
            row[
                "evaporation_delta_pp_to_reference"
            ] = None
            row[
                "stranded_delta_pp_to_reference"
            ] = None

            if (
                reference is None
                or row.get(
                    "final_center_longitude"
                )
                is None
                or row.get(
                    "final_center_latitude"
                )
                is None
            ):
                continue

            row[
                "center_delta_km_to_reference"
            ] = round(
                haversine_km(
                    row[
                        "final_center_longitude"
                    ],
                    row[
                        "final_center_latitude"
                    ],
                    reference[
                        "final_center_longitude"
                    ],
                    reference[
                        "final_center_latitude"
                    ],
                ),
                3,
            )

            if (
                row.get(
                    "evaporated_percent"
                )
                is not None
                and reference.get(
                    "evaporated_percent"
                )
                is not None
            ):
                row[
                    "evaporation_delta_pp_to_reference"
                ] = round(
                    float(
                        row[
                            "evaporated_percent"
                        ]
                    )
                    - float(
                        reference[
                            "evaporated_percent"
                        ]
                    ),
                    4,
                )

            if (
                row.get(
                    "stranded_percent"
                )
                is not None
                and reference.get(
                    "stranded_percent"
                )
                is not None
            ):
                row[
                    "stranded_delta_pp_to_reference"
                ] = round(
                    float(
                        row[
                            "stranded_percent"
                        ]
                    )
                    - float(
                        reference[
                            "stranded_percent"
                        ]
                    ),
                    4,
                )


def _serializable_case(
    case: ValidationCase,
) -> dict:
    result = asdict(
        case
    )
    return result


def write_json(
    path: Path,
    payload,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_csv(
    path: Path,
    rows: list[dict],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = []

    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(
                    key
                )

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(
            rows
        )


def format_optional(
    value,
    *,
    digits: int = 2,
) -> str:
    if value is None:
        return "—"

    if isinstance(
        value,
        float,
    ):
        return f"{value:.{digits}f}"

    return str(value)


def build_text_summary(
    *,
    profile: str,
    at_iso: str,
    rows: list[dict],
    elapsed_seconds: float,
) -> str:
    lines = [
        "OPENOIL VALIDATION MATRIX",
        "",
        f"Profile: {profile}",
        f"Start time: {at_iso}",
        f"Cases: {len(rows)}",
        f"Total runtime: {elapsed_seconds / 60:.1f} min",
        "",
    ]

    health_counts: dict[
        str,
        int,
    ] = {}

    for row in rows:
        health = str(
            row.get(
                "health_status",
                "UNKNOWN",
            )
        )
        health_counts[
            health
        ] = health_counts.get(
            health,
            0,
        ) + 1

    lines.append(
        "HEALTH"
    )

    for key in sorted(
        health_counts
    ):
        lines.append(
            f"{key}: {health_counts[key]}"
        )

    lines.extend(
        [
            "",
            "CASES",
        ]
    )

    for row in rows:
        lines.append(
            " | ".join(
                [
                    str(
                        row.get(
                            "case_id"
                        )
                    ),
                    str(
                        row.get(
                            "health_status"
                        )
                    ),
                    (
                        "complete="
                        + str(
                            row.get(
                                "forecast_complete"
                            )
                        )
                    ),
                    (
                        "reason="
                        + str(
                            row.get(
                                "completion_reason"
                            )
                        )
                    ),
                    (
                        "stranded="
                        + format_optional(
                            row.get(
                                "stranded_percent"
                            )
                        )
                        + "%"
                    ),
                    (
                        "evap="
                        + format_optional(
                            row.get(
                                "evaporated_percent"
                            )
                        )
                        + "%"
                    ),
                    (
                        "center_delta_ref="
                        + format_optional(
                            row.get(
                                "center_delta_km_to_reference"
                            ),
                            digits=3,
                        )
                        + "km"
                    ),
                    (
                        "mass_err="
                        + format_optional(
                            row.get(
                                "mass_closure_error_percent"
                            ),
                            digits=6,
                        )
                        + "%"
                    ),
                    (
                        "runtime="
                        + format_optional(
                            row.get(
                                "runtime_seconds"
                            ),
                            digits=1,
                        )
                        + "s"
                    ),
                ]
            )
        )

        if row.get(
            "error"
        ):
            lines.append(
                f"  ERROR: {row['error']}"
            )

    lines.extend(
        [
            "",
            "REFERENCE RULE",
            (
                "For each scenario + forecast horizon, the reference is the "
                "successful case with the highest particle count and widest "
                "forcing box available in this run."
            ),
            "",
            "INTERPRETATION",
            (
                "center_delta_km_to_reference, evaporation_delta_pp_to_reference "
                "and stranded_delta_pp_to_reference are sensitivity diagnostics. "
                "No scientific pass/fail threshold is imposed yet."
            ),
            (
                f"Mass-balance warning threshold is an internal engineering "
                f"check of {MASS_BALANCE_WARNING_PERCENT}%."
            ),
            "",
        ]
    )

    return "\n".join(
        lines
    )


def run_validation_matrix(
    *,
    profile: str,
    at: str | datetime | None,
    output_dir: Path,
    scenario_keys: Iterable[str] | None = None,
    resume: bool = True,
    progress_callback=None,
) -> dict:
    cases = build_validation_cases(
        profile=profile,
        scenario_keys=scenario_keys,
    )

    matrix_time = normalize_target_time(
        at
    )
    at_iso = matrix_time.isoformat()

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    case_dir = (
        output_dir
        / "cases"
    )
    case_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    progress_log = (
        output_dir
        / "progress.log"
    )

    rows: list[dict] = []

    matrix_started = time.perf_counter()

    def progress(
        message: str,
    ) -> None:
        stamp = datetime.now(
            timezone.utc
        ).isoformat()

        line = (
            f"{stamp} {message}"
        )

        with progress_log.open(
            "a",
            encoding="utf-8",
        ) as handle:
            handle.write(
                line + "\n"
            )

        if progress_callback:
            progress_callback(
                message
            )

    progress(
        f"matrix_start profile={profile} cases={len(cases)} at={at_iso}"
    )

    for index, case in enumerate(
        cases,
        start=1,
    ):
        identifier = case_id(
            case
        )
        result_path = (
            case_dir
            / f"{identifier}.json"
        )

        progress(
            f"[{index}/{len(cases)}] start {identifier}"
        )

        if (
            resume
            and result_path.exists()
        ):
            try:
                stored = json.loads(
                    result_path.read_text(
                        encoding="utf-8"
                    )
                )

                if (
                    stored.get(
                        "matrix_at"
                    )
                    == at_iso
                    and stored.get(
                        "summary"
                    )
                ):
                    rows.append(
                        stored[
                            "summary"
                        ]
                    )
                    progress(
                        f"[{index}/{len(cases)}] resume {identifier}"
                    )
                    continue
            except (
                OSError,
                json.JSONDecodeError,
            ):
                pass

        started = time.perf_counter()

        try:
            payload = run_dynamic_openoil(
                longitude=(
                    case.scenario.longitude
                ),
                latitude=(
                    case.scenario.latitude
                ),
                at=at_iso,
                hours=case.hours,
                particles=case.particles,
                radius_m=case.radius_m,
                release_volume_m3=(
                    case.release_volume_m3
                ),
                half_width_deg=(
                    case.half_width_deg
                ),
            )

            runtime_seconds = (
                time.perf_counter()
                - started
            )

            summary = summarize_payload(
                case=case,
                payload=payload,
                runtime_seconds=(
                    runtime_seconds
                ),
            )

            stored = {
                "matrix_at": at_iso,
                "case": (
                    _serializable_case(
                        case
                    )
                ),
                "summary": summary,
                "payload": payload,
            }

            write_json(
                result_path,
                stored,
            )

            rows.append(
                summary
            )

            progress(
                f"[{index}/{len(cases)}] done {identifier} "
                f"health={summary['health_status']} "
                f"runtime={runtime_seconds:.1f}s"
            )

        except Exception as exc:
            runtime_seconds = (
                time.perf_counter()
                - started
            )

            summary = error_summary(
                case=case,
                error=exc,
                runtime_seconds=(
                    runtime_seconds
                ),
            )

            write_json(
                result_path,
                {
                    "matrix_at": at_iso,
                    "case": (
                        _serializable_case(
                            case
                        )
                    ),
                    "summary": summary,
                    "payload": None,
                },
            )

            rows.append(
                summary
            )

            progress(
                f"[{index}/{len(cases)}] error {identifier} "
                f"{summary['error']}"
            )

    add_reference_deltas(
        rows
    )

    elapsed_seconds = (
        time.perf_counter()
        - matrix_started
    )

    result = {
        "profile": profile,
        "matrix_at": at_iso,
        "scenario_keys": [
            scenario.key
            for scenario in select_scenarios(
                scenario_keys
            )
        ],
        "case_count": len(
            rows
        ),
        "elapsed_seconds": round(
            elapsed_seconds,
            2,
        ),
        "rows": rows,
    }

    write_json(
        output_dir
        / "results.json",
        result,
    )

    write_csv(
        output_dir
        / "summary.csv",
        rows,
    )

    (
        output_dir
        / "summary.txt"
    ).write_text(
        build_text_summary(
            profile=profile,
            at_iso=at_iso,
            rows=rows,
            elapsed_seconds=(
                elapsed_seconds
            ),
        ),
        encoding="utf-8",
    )

    progress(
        f"matrix_done cases={len(rows)} runtime={elapsed_seconds:.1f}s"
    )

    return result
