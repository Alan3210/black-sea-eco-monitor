from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
DRIFT = REPO_ROOT / "agents" / "ocean_data" / "drift_forecast.py"
API = REPO_ROOT / "backend" / "api" / "ocean_drift.py"
BACKUP_DIR = REPO_ROOT / "dev-snapshots"

MARKER = "WEATHER1_3B_CURRENTS_PLUS_WIND"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f"marker not found: {label}")
    return text.replace(old, new, 1)


def backup(path: Path, label: str) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = (
        BACKUP_DIR
        / f"{label}.before_weather1_3b_{stamp}{path.suffix}"
    )
    shutil.copy2(path, target)
    return target


def patch_drift(text: str) -> str:
    if MARKER in text:
        return text

    constants_marker = """FORCING_MARGIN_DEG = 4.0

MIN_PARTICLES = 50
"""
    constants_new = """FORCING_MARGIN_DEG = 4.0

# WEATHER1_3B_CURRENTS_PLUS_WIND
FORCING_MODE_CURRENT_ONLY = "current_only"
FORCING_MODE_CURRENTS_PLUS_WIND = "currents_plus_wind"
SUPPORTED_FORCING_MODES = (
    FORCING_MODE_CURRENT_ONLY,
    FORCING_MODE_CURRENTS_PLUS_WIND,
)
DEFAULT_FORCING_MODE = FORCING_MODE_CURRENT_ONLY
DEFAULT_WIND_DRIFT_FACTOR = 0.02

MIN_PARTICLES = 50
"""
    text = replace_once(
        text,
        constants_marker,
        constants_new,
        "forcing mode constants",
    )

    input_class_marker = """class OceanDriftInputError(ValueError):
    pass


def _utc_now() -> datetime:
"""
    input_class_new = """class OceanDriftInputError(ValueError):
    pass


def normalize_forcing_mode(
    value: str | None,
) -> str:
    mode = str(value or DEFAULT_FORCING_MODE).strip().lower()

    if mode not in SUPPORTED_FORCING_MODES:
        raise OceanDriftInputError(
            "forcing_mode must be one of: "
            + ", ".join(SUPPORTED_FORCING_MODES)
            + "."
        )

    return mode


def drift_scope(
    forcing_mode: str,
) -> str:
    mode = normalize_forcing_mode(forcing_mode)

    if mode == FORCING_MODE_CURRENTS_PLUS_WIND:
        return (
            "passive_surface_tracer_currents_plus_direct_windage"
        )

    return "passive_surface_tracer_current_only"


def wind_drift_factor_for_mode(
    forcing_mode: str,
) -> float:
    mode = normalize_forcing_mode(forcing_mode)

    if mode == FORCING_MODE_CURRENTS_PLUS_WIND:
        return DEFAULT_WIND_DRIFT_FACTOR

    return 0.0


def _utc_now() -> datetime:
"""
    text = replace_once(
        text,
        input_class_marker,
        input_class_new,
        "forcing helpers",
    )

    cache_sig_old = """def _cache_key(
    *,
    start_time: datetime,
    longitude: float,
    latitude: float,
    hours: int,
    particles: int,
    radius_m: float,
    diffusivity_m2_s: float,
) -> str:
"""
    cache_sig_new = """def _cache_key(
    *,
    start_time: datetime,
    longitude: float,
    latitude: float,
    hours: int,
    particles: int,
    radius_m: float,
    diffusivity_m2_s: float,
    forcing_mode: str = DEFAULT_FORCING_MODE,
) -> str:
"""
    text = replace_once(
        text,
        cache_sig_old,
        cache_sig_new,
        "cache key signature",
    )

    cache_json_old = """"diffusivity_m2_s": round(
                diffusivity_m2_s,
                3,
            ),
        },
"""
    cache_json_new = """"diffusivity_m2_s": round(
                diffusivity_m2_s,
                3,
            ),
            "forcing_mode": normalize_forcing_mode(
                forcing_mode
            ),
        },
"""
    text = replace_once(
        text,
        cache_json_old,
        cache_json_new,
        "cache key forcing mode",
    )

    run_sig_old = """def _run_opendrift(
    *,
    dataset,
    start_time: datetime,
    longitude: float,
    latitude: float,
    hours: int,
    particles: int,
    radius_m: float,
    diffusivity_m2_s: float,
):
"""
    run_sig_new = """def _run_opendrift(
    *,
    dataset,
    start_time: datetime,
    longitude: float,
    latitude: float,
    hours: int,
    particles: int,
    radius_m: float,
    diffusivity_m2_s: float,
    wind_reader=None,
    wind_drift_factor: float = 0.0,
):
"""
    text = replace_once(
        text,
        run_sig_old,
        run_sig_new,
        "run opendrift signature",
    )

    add_reader_old = """    model.add_reader(reader)

    # v0.9 Step 1 = current-only passive surface tracer.
"""
    add_reader_new = """    model.add_reader(reader)

    if wind_reader is not None:
        model.add_reader(wind_reader)

    # Surface tracer: currents are always enabled.
    # WEATHER-1.3B optionally adds direct windage through OpenDrift.
"""
    text = replace_once(
        text,
        add_reader_old,
        add_reader_new,
        "wind reader registration",
    )

    seed_old = """        z=0,
        wind_drift_factor=0.0,
        current_drift_factor=1.0,
"""
    seed_new = """        z=0,
        wind_drift_factor=float(wind_drift_factor),
        current_drift_factor=1.0,
"""
    text = replace_once(
        text,
        seed_old,
        seed_new,
        "seed wind drift factor",
    )

    payload_sig_old = """def build_drift_payload(
    result,
    *,
    start_time: datetime,
    longitude: float,
    latitude: float,
    hours: int,
    particles: int,
    radius_m: float,
    diffusivity_m2_s: float,
    opendrift_version: str | None = None,
) -> dict:
"""
    payload_sig_new = """def build_drift_payload(
    result,
    *,
    start_time: datetime,
    longitude: float,
    latitude: float,
    hours: int,
    particles: int,
    radius_m: float,
    diffusivity_m2_s: float,
    opendrift_version: str | None = None,
    forcing_mode: str = DEFAULT_FORCING_MODE,
    wind_forcing_provenance: dict | None = None,
) -> dict:
"""
    text = replace_once(
        text,
        payload_sig_old,
        payload_sig_new,
        "payload signature",
    )

    payload_preamble_old = """    snapshots = [
        _snapshot(
"""
    payload_preamble_new = """    forcing_mode = normalize_forcing_mode(
        forcing_mode
    )
    wind_factor = wind_drift_factor_for_mode(
        forcing_mode
    )

    not_included = [
        "wave / Stokes drift",
        "oil weathering",
        "evaporation",
        "emulsification",
        "oil viscosity changes",
    ]

    if forcing_mode == FORCING_MODE_CURRENT_ONLY:
        not_included.insert(0, "wind forcing")

    snapshots = [
        _snapshot(
"""
    text = replace_once(
        text,
        payload_preamble_old,
        payload_preamble_new,
        "payload preamble",
    )

    scope_old = """"scope": (
            "passive_surface_tracer_current_only"
        ),
        "forcing": {
"""
    scope_new = """"scope": drift_scope(forcing_mode),
        "forcing_mode": forcing_mode,
        "forcing": {
"""
    text = replace_once(
        text,
        scope_old,
        scope_new,
        "payload scope",
    )

    forcing_bbox_old = """"bbox": forcing_bbox(
                longitude=longitude,
                latitude=latitude,
            ),
        },
"""
    forcing_bbox_new = """"bbox": forcing_bbox(
                longitude=longitude,
                latitude=latitude,
            ),
            "wind": (
                wind_forcing_provenance
                if forcing_mode
                == FORCING_MODE_CURRENTS_PLUS_WIND
                else {
                    "enabled": False,
                    "reason": "current_only forcing mode",
                }
            ),
        },
"""
    text = replace_once(
        text,
        forcing_bbox_old,
        forcing_bbox_new,
        "wind forcing provenance",
    )

    simulation_old = """"wind_drift_factor": 0.0,
            "current_drift_factor": 1.0,
"""
    simulation_new = """"wind_drift_factor": float(
                wind_factor
            ),
            "current_drift_factor": 1.0,
"""
    text = replace_once(
        text,
        simulation_old,
        simulation_new,
        "payload wind factor",
    )

    not_included_old = """"not_included": [
            "wind forcing",
            "wave / Stokes drift",
            "oil weathering",
            "evaporation",
            "emulsification",
            "oil viscosity changes",
        ],
"""
    not_included_new = """"not_included": not_included,
"""
    text = replace_once(
        text,
        not_included_old,
        not_included_new,
        "conditional not included",
    )

    surface_sig_old = """def run_surface_drift(
    *,
    longitude: float,
    latitude: float,
    at: str | datetime | None = None,
    hours: int = DEFAULT_HOURS,
    particles: int = DEFAULT_PARTICLES,
    radius_m: float = DEFAULT_RADIUS_M,
    diffusivity_m2_s: float = DEFAULT_DIFFUSIVITY_M2_S,
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
) -> dict:
"""
    surface_sig_new = """def run_surface_drift(
    *,
    longitude: float,
    latitude: float,
    at: str | datetime | None = None,
    hours: int = DEFAULT_HOURS,
    particles: int = DEFAULT_PARTICLES,
    radius_m: float = DEFAULT_RADIUS_M,
    diffusivity_m2_s: float = DEFAULT_DIFFUSIVITY_M2_S,
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
    forcing_mode: str = DEFAULT_FORCING_MODE,
) -> dict:
"""
    text = replace_once(
        text,
        surface_sig_old,
        surface_sig_new,
        "run surface signature",
    )

    start_time_old = """    start_time = normalize_target_time(
        at
    )

    cache_path = _cache_path(
"""
    start_time_new = """    forcing_mode = normalize_forcing_mode(
        forcing_mode
    )

    start_time = normalize_target_time(
        at
    )

    cache_path = _cache_path(
"""
    text = replace_once(
        text,
        start_time_old,
        start_time_new,
        "normalize forcing mode",
    )

    cache_call_old = """        diffusivity_m2_s=diffusivity_m2_s,
    )

    cached = _read_cache(
"""
    cache_call_new = """        diffusivity_m2_s=diffusivity_m2_s,
        forcing_mode=forcing_mode,
    )

    cached = _read_cache(
"""
    text = replace_once(
        text,
        cache_call_old,
        cache_call_new,
        "cache mode argument",
    )

    dataset_init_old = """    dataset = None

    try:
        dataset = _open_forcing_dataset(
"""
    dataset_init_new = """    dataset = None
    wind_forcing = None
    wind_reader = None
    wind_forcing_provenance = None

    try:
        dataset = _open_forcing_dataset(
"""
    text = replace_once(
        text,
        dataset_init_old,
        dataset_init_new,
        "wind forcing init",
    )

    before_run_old = """        result = _run_opendrift(
            dataset=dataset,
"""
    before_run_new = """        if (
            forcing_mode
            == FORCING_MODE_CURRENTS_PLUS_WIND
        ):
            try:
                from backend.services.ecmwf_wind_forcing import (
                    EcmwfWindForcingBuilder,
                    build_opendrift_wind_reader,
                )
            except ImportError as exc:
                raise OceanDriftError(
                    "WEATHER-1.3A wind forcing module "
                    "is not available."
                ) from exc

            wind_forcing = (
                EcmwfWindForcingBuilder().build(
                    start_time=start_time,
                    hours=hours,
                    bbox=forcing_bbox(
                        longitude=longitude,
                        latitude=latitude,
                    ),
                )
            )
            wind_reader = build_opendrift_wind_reader(
                wind_forcing
            )
            wind_forcing_provenance = (
                wind_forcing.provenance()
            )

        result = _run_opendrift(
            dataset=dataset,
"""
    text = replace_once(
        text,
        before_run_old,
        before_run_new,
        "build wind forcing",
    )

    run_args_old = """            diffusivity_m2_s=diffusivity_m2_s,
        )

        try:
"""
    run_args_new = """            diffusivity_m2_s=diffusivity_m2_s,
            wind_reader=wind_reader,
            wind_drift_factor=(
                wind_drift_factor_for_mode(
                    forcing_mode
                )
            ),
        )

        try:
"""
    text = replace_once(
        text,
        run_args_old,
        run_args_new,
        "run wind args",
    )

    payload_args_old = """            diffusivity_m2_s=diffusivity_m2_s,
            opendrift_version=version,
        )
"""
    payload_args_new = """            diffusivity_m2_s=diffusivity_m2_s,
            opendrift_version=version,
            forcing_mode=forcing_mode,
            wind_forcing_provenance=(
                wind_forcing_provenance
            ),
        )
"""
    text = replace_once(
        text,
        payload_args_old,
        payload_args_new,
        "payload mode args",
    )

    finally_old = """    finally:
        if (
            dataset is not None
            and hasattr(
                dataset,
                "close",
            )
        ):
            dataset.close()
"""
    finally_new = """    finally:
        if (
            wind_forcing is not None
            and hasattr(
                wind_forcing.dataset,
                "close",
            )
        ):
            wind_forcing.dataset.close()

        if (
            dataset is not None
            and hasattr(
                dataset,
                "close",
            )
        ):
            dataset.close()
"""
    text = replace_once(
        text,
        finally_old,
        finally_new,
        "close wind dataset",
    )

    return text


def patch_api(text: str) -> str:
    import_marker = """    DEFAULT_DIFFUSIVITY_M2_S,
    DEFAULT_HOURS,
    DEFAULT_PARTICLES,
"""
    import_new = """    DEFAULT_DIFFUSIVITY_M2_S,
    DEFAULT_FORCING_MODE,
    DEFAULT_HOURS,
    DEFAULT_PARTICLES,
"""
    text = replace_once(
        text,
        import_marker,
        import_new,
        "api default mode import",
    )

    supported_marker = """    STANDARD_HORIZONS_HOURS,
    run_surface_drift,
)
"""
    supported_new = """    STANDARD_HORIZONS_HOURS,
    SUPPORTED_FORCING_MODES,
    run_surface_drift,
)
"""
    text = replace_once(
        text,
        supported_marker,
        supported_new,
        "api supported mode import",
    )

    mode_insert_marker = """    particles: int = Query(
        default=DEFAULT_PARTICLES,
"""
    mode_insert_new = """    forcing_mode: str = Query(
        default=DEFAULT_FORCING_MODE,
        description=(
            "Environmental forcing mode. Supported values: "
            + ", ".join(SUPPORTED_FORCING_MODES)
            + ". current_only is the backward-compatible default."
        ),
    ),
    particles: int = Query(
        default=DEFAULT_PARTICLES,
"""
    text = replace_once(
        text,
        mode_insert_marker,
        mode_insert_new,
        "api forcing mode query",
    )

    call_marker = """            diffusivity_m2_s=diffusivity_m2_s,
        )
"""
    call_new = """            diffusivity_m2_s=diffusivity_m2_s,
            forcing_mode=forcing_mode,
        )
"""
    text = replace_once(
        text,
        call_marker,
        call_new,
        "api forcing mode call",
    )

    return text


def main() -> int:
    prerequisites = [
        DRIFT,
        API,
        REPO_ROOT / "backend/services/ecmwf_wind_forcing.py",
    ]

    for path in prerequisites:
        if not path.exists():
            print(f"ERROR: prerequisite missing: {path}")
            return 2

    drift_text = DRIFT.read_text(encoding="utf-8")
    api_text = API.read_text(encoding="utf-8")

    if MARKER in drift_text:
        print("WEATHER-1.3B currents+wind already installed.")
        return 0

    try:
        updated_drift = patch_drift(drift_text)
        updated_api = patch_api(api_text)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        print("No runtime file was modified.")
        return 3

    backups = [
        backup(DRIFT, "drift_forecast"),
        backup(API, "ocean_drift_api"),
    ]

    DRIFT.write_text(updated_drift, encoding="utf-8")
    API.write_text(updated_api, encoding="utf-8")

    print("WEATHER-1.3B Currents + Wind v0.1 installed.")
    print("Modified:")
    print("  agents/ocean_data/drift_forecast.py")
    print("  backend/api/ocean_drift.py")
    print("Behavior:")
    print("  current_only remains the default")
    print("  currents_plus_wind adds ECMWF x_wind/y_wind")
    print("  OpenDrift applies wind_drift_factor=0.02")
    print("  Stokes drift and oil weathering remain excluded")
    print("Backups:")
    for item in backups:
        print(f"  {item.relative_to(REPO_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
