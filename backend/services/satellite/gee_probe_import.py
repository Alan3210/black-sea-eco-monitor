from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.news_agent.event_store import EventStore


OBSERVATION_TYPE = "sar_scene"
SENSOR = "Sentinel-1"
PROCESSING_METHOD = "gee_sentinel1_probe"


class GeeProbeImportError(ValueError):
    """Raised when a cached GEE probe cannot be mapped safely."""


def load_probe(path: str | Path) -> dict[str, Any]:
    probe_path = Path(path)

    try:
        payload = json.loads(
            probe_path.read_text(encoding="utf-8")
        )
    except FileNotFoundError as exc:
        raise GeeProbeImportError(
            f"probe file not found: {probe_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise GeeProbeImportError(
            f"invalid probe JSON: {probe_path}"
        ) from exc

    if not isinstance(payload, dict):
        raise GeeProbeImportError(
            "probe root must be a JSON object"
        )

    return payload


def _collect_positions(
    value: Any,
    positions: list[tuple[float, float]],
) -> None:
    if (
        isinstance(value, (list, tuple))
        and len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    ):
        positions.append(
            (float(value[0]), float(value[1]))
        )
        return

    if isinstance(value, (list, tuple)):
        for item in value:
            _collect_positions(
                item,
                positions,
            )


def derive_bbox_from_geometry(
    geometry: dict[str, Any],
) -> tuple[float, float, float, float]:
    if not isinstance(geometry, dict):
        raise GeeProbeImportError(
            "scene footprint must be a GeoJSON object"
        )

    coordinates = geometry.get("coordinates")
    positions: list[tuple[float, float]] = []

    _collect_positions(
        coordinates,
        positions,
    )

    if not positions:
        raise GeeProbeImportError(
            "scene footprint contains no coordinates"
        )

    longitudes = [
        position[0]
        for position in positions
    ]
    latitudes = [
        position[1]
        for position in positions
    ]

    return (
        min(longitudes),
        min(latitudes),
        max(longitudes),
        max(latitudes),
    )


def build_observation_kwargs(
    probe: dict[str, Any],
    *,
    scene_index: int = 0,
) -> dict[str, Any]:
    if probe.get("information_type") != (
        "satellite_observation"
    ):
        raise GeeProbeImportError(
            "probe information_type must be "
            "'satellite_observation'"
        )

    scenes = probe.get("scenes")

    if not isinstance(scenes, list) or not scenes:
        raise GeeProbeImportError(
            "probe contains no saved scenes"
        )

    if scene_index < 0 or scene_index >= len(scenes):
        raise GeeProbeImportError(
            f"scene_index out of range: {scene_index}"
        )

    scene = scenes[scene_index]

    if not isinstance(scene, dict):
        raise GeeProbeImportError(
            "scene must be a JSON object"
        )

    query = probe.get("query")
    if not isinstance(query, dict):
        raise GeeProbeImportError(
            "probe query must be a JSON object"
        )

    dataset_id = query.get("dataset_id")
    scene_id = scene.get("scene_id")
    acquisition_time = scene.get(
        "acquisition_time"
    )
    geometry = scene.get("footprint_bounds")

    for field_name, value in {
        "dataset_id": dataset_id,
        "scene_id": scene_id,
        "acquisition_time": acquisition_time,
    }.items():
        if not isinstance(value, str) or not value.strip():
            raise GeeProbeImportError(
                f"missing or invalid {field_name}"
            )

    if not isinstance(geometry, dict):
        raise GeeProbeImportError(
            "missing or invalid footprint_bounds"
        )

    (
        min_lon,
        min_lat,
        max_lon,
        max_lat,
    ) = derive_bbox_from_geometry(
        geometry
    )

    probe_version = str(
        probe.get("probe_version") or "0.1"
    )

    provenance = dict(
        probe.get("provenance") or {}
    )

    provenance.update(
        {
            "probe_version": probe_version,
            "probe_aoi": probe.get("aoi"),
            "probe_query": query,
            "scene_metadata": {
                "instrument_mode": scene.get(
                    "instrument_mode"
                ),
                "orbit_pass": scene.get(
                    "orbit_pass"
                ),
                "polarizations": scene.get(
                    "polarizations"
                ),
                "relative_orbit": scene.get(
                    "relative_orbit"
                ),
                "resolution_meters": scene.get(
                    "resolution_meters"
                ),
                "system_index": scene.get(
                    "system_index"
                ),
            },
        }
    )

    return {
        "observation_type": OBSERVATION_TYPE,
        "sensor": SENSOR,
        "platform": scene.get(
            "platform_number"
        ),
        "dataset_id": dataset_id.strip(),
        "source_image_id": scene_id.strip(),
        "acquisition_time": acquisition_time,
        "derivation_level": probe.get(
            "derivation_level",
            "processed",
        ),
        "processing_time": probe.get(
            "generated_at"
        ),
        "geometry": geometry,
        "bbox_min_lon": min_lon,
        "bbox_min_lat": min_lat,
        "bbox_max_lon": max_lon,
        "bbox_max_lat": max_lat,
        "confidence": None,
        "review_status": "unreviewed",
        "processing_version": probe_version,
        "processing_method": PROCESSING_METHOD,
        "cache_reference": None,
        "provenance": provenance,
    }


def find_existing_observation_id(
    store: EventStore,
    *,
    source_image_id: str,
    processing_version: str,
    observation_type: str,
) -> str | None:
    for observation in (
        store.list_satellite_observations()
    ):
        if (
            observation.get("source_image_id")
            == source_image_id
            and observation.get(
                "processing_version"
            )
            == processing_version
            and observation.get(
                "observation_type"
            )
            == observation_type
        ):
            return observation["id"]

    return None


def import_probe_scene(
    store: EventStore,
    probe: dict[str, Any],
    *,
    scene_index: int = 0,
) -> dict[str, Any]:
    kwargs = build_observation_kwargs(
        probe,
        scene_index=scene_index,
    )

    existing_id = find_existing_observation_id(
        store,
        source_image_id=kwargs[
            "source_image_id"
        ],
        processing_version=kwargs[
            "processing_version"
        ],
        observation_type=kwargs[
            "observation_type"
        ],
    )

    if existing_id is not None:
        return {
            "created": False,
            "observation_id": existing_id,
            "source_image_id": kwargs[
                "source_image_id"
            ],
            "acquisition_time": kwargs[
                "acquisition_time"
            ],
            "dataset_id": kwargs[
                "dataset_id"
            ],
        }

    observation_id = (
        store.create_satellite_observation(
            **kwargs
        )
    )

    return {
        "created": True,
        "observation_id": observation_id,
        "source_image_id": kwargs[
            "source_image_id"
        ],
        "acquisition_time": kwargs[
            "acquisition_time"
        ],
        "dataset_id": kwargs[
            "dataset_id"
        ],
    }


def import_probe_file(
    store: EventStore,
    probe_path: str | Path,
    *,
    scene_index: int = 0,
) -> dict[str, Any]:
    probe = load_probe(
        probe_path
    )

    return import_probe_scene(
        store,
        probe,
        scene_index=scene_index,
    )
