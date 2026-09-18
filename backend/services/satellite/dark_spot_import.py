from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.news_agent.event_store import EventStore


OBSERVATION_TYPE = "sar_dark_spot_candidate"
SENSOR = "Sentinel-1"
DEFAULT_DATASET_ID = "COPERNICUS/S1_GRD"
PROCESSING_METHOD = "gee_sentinel1_dark_spot_candidates"


class DarkSpotImportError(ValueError):
    """Raised when SAT-7B candidate data cannot be imported safely."""


def load_candidate_payload(
    path: str | Path,
) -> dict[str, Any]:
    payload_path = Path(path)

    try:
        payload = json.loads(
            payload_path.read_text(
                encoding="utf-8"
            )
        )
    except FileNotFoundError as exc:
        raise DarkSpotImportError(
            f"candidate file not found: {payload_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise DarkSpotImportError(
            f"invalid candidate JSON: {payload_path}"
        ) from exc

    if not isinstance(payload, dict):
        raise DarkSpotImportError(
            "candidate payload root must be a JSON object"
        )

    return payload


def validate_candidate_payload(
    payload: dict[str, Any],
) -> None:
    if payload.get("information_type") != (
        "satellite_observation"
    ):
        raise DarkSpotImportError(
            "information_type must be "
            "'satellite_observation'"
        )

    if payload.get("derivation_level") != "derived":
        raise DarkSpotImportError(
            "derivation_level must be 'derived'"
        )

    if payload.get("observation_type") != (
        OBSERVATION_TYPE
    ):
        raise DarkSpotImportError(
            "observation_type must be "
            f"'{OBSERVATION_TYPE}'"
        )

    source_scene = payload.get(
        "source_scene"
    )

    if not isinstance(
        source_scene,
        dict,
    ):
        raise DarkSpotImportError(
            "source_scene must be an object"
        )

    for field_name in (
        "scene_id",
        "acquisition_time",
    ):
        value = source_scene.get(
            field_name
        )

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise DarkSpotImportError(
                f"source_scene missing {field_name}"
            )

    candidates = payload.get(
        "candidates"
    )

    if not isinstance(
        candidates,
        list,
    ):
        raise DarkSpotImportError(
            "candidates must be a list"
        )


def _bbox_values(
    candidate: dict[str, Any],
) -> tuple[
    float,
    float,
    float,
    float,
]:
    bbox = candidate.get(
        "bbox"
    )

    if (
        not isinstance(bbox, list)
        or len(bbox) != 4
    ):
        raise DarkSpotImportError(
            "candidate bbox must contain four values"
        )

    try:
        min_lon, min_lat, max_lon, max_lat = [
            float(value)
            for value in bbox
        ]
    except (TypeError, ValueError) as exc:
        raise DarkSpotImportError(
            "candidate bbox values must be numeric"
        ) from exc

    if (
        min_lon >= max_lon
        or min_lat >= max_lat
    ):
        raise DarkSpotImportError(
            "candidate bbox has invalid bounds"
        )

    return (
        min_lon,
        min_lat,
        max_lon,
        max_lat,
    )


def build_observation_kwargs(
    payload: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    validate_candidate_payload(
        payload
    )

    if not isinstance(
        candidate,
        dict,
    ):
        raise DarkSpotImportError(
            "candidate must be an object"
        )

    candidate_id = candidate.get(
        "candidate_id"
    )

    if (
        not isinstance(candidate_id, str)
        or not candidate_id.strip()
    ):
        raise DarkSpotImportError(
            "candidate missing candidate_id"
        )

    geometry = candidate.get(
        "geometry"
    )

    if not isinstance(
        geometry,
        dict,
    ):
        raise DarkSpotImportError(
            f"{candidate_id}: geometry must be an object"
        )

    (
        min_lon,
        min_lat,
        max_lon,
        max_lat,
    ) = _bbox_values(
        candidate
    )

    source_scene = payload[
        "source_scene"
    ]
    analysis = payload.get(
        "analysis"
    ) or {}
    provenance = payload.get(
        "provenance"
    ) or {}
    semantics = payload.get(
        "semantics"
    ) or {}

    processing_version = str(
        payload.get(
            "extraction_version"
        )
        or "0.1"
    )

    dataset_id = (
        provenance.get(
            "dataset_id"
        )
        or DEFAULT_DATASET_ID
    )

    candidate_provenance = {
        "candidate_id": candidate_id,
        "area_km2": candidate.get(
            "area_km2"
        ),
        "mean_vv_db": candidate.get(
            "mean_vv_db"
        ),
        "source_scene_id": source_scene.get(
            "scene_id"
        ),
        "source_system_index": source_scene.get(
            "system_index"
        ),
        "source_orbit_pass": source_scene.get(
            "orbit_pass"
        ),
        "source_relative_orbit": source_scene.get(
            "relative_orbit"
        ),
        "threshold_db": analysis.get(
            "threshold_db"
        ),
        "edge_noise_floor_db": analysis.get(
            "edge_noise_floor_db"
        ),
        "min_area_km2": analysis.get(
            "min_area_km2"
        ),
        "min_connected_pixels": analysis.get(
            "min_connected_pixels"
        ),
        "connectivity": analysis.get(
            "connectivity"
        ),
        "scale_meters": analysis.get(
            "scale_meters"
        ),
        "water_mask": analysis.get(
            "water_mask"
        ),
        "data_provider": provenance.get(
            "data_provider"
        ),
        "processing_platform": provenance.get(
            "processing_platform"
        ),
        "source_level": provenance.get(
            "source_level"
        ),
        "gee_representation": provenance.get(
            "gee_representation"
        ),
        "source_processing_method": provenance.get(
            "processing_method"
        ),
        "semantic_disclaimer": {
            "result_type": semantics.get(
                "result_type",
                OBSERVATION_TYPE,
            ),
            "does_not_mean": semantics.get(
                "does_not_mean",
                [
                    "oil_spill",
                    "confirmed_pollution",
                    "confirmed_event",
                    "causal_link_to_event",
                ],
            ),
        },
    }

    return {
        "observation_type": (
            OBSERVATION_TYPE
        ),
        "sensor": SENSOR,
        "platform": source_scene.get(
            "platform_number"
        ),
        "dataset_id": str(
            dataset_id
        ),
        "source_image_id": source_scene[
            "scene_id"
        ],
        "acquisition_time": source_scene[
            "acquisition_time"
        ],
        "derivation_level": "derived",
        "processing_time": payload.get(
            "generated_at"
        ),
        "geometry": geometry,
        "bbox_min_lon": min_lon,
        "bbox_min_lat": min_lat,
        "bbox_max_lon": max_lon,
        "bbox_max_lat": max_lat,
        "confidence": None,
        "review_status": (
            candidate.get(
                "review_status"
            )
            or "unreviewed"
        ),
        "processing_version": (
            processing_version
        ),
        "processing_method": (
            PROCESSING_METHOD
        ),
        "cache_reference": None,
        "provenance": (
            candidate_provenance
        ),
    }


def find_existing_candidate_observation_id(
    store: EventStore,
    *,
    source_image_id: str,
    processing_version: str,
    candidate_id: str,
) -> str | None:
    for observation in (
        store.list_satellite_observations()
    ):
        if observation.get(
            "source_image_id"
        ) != source_image_id:
            continue

        if observation.get(
            "observation_type"
        ) != OBSERVATION_TYPE:
            continue

        if observation.get(
            "processing_version"
        ) != processing_version:
            continue

        provenance = observation.get(
            "provenance"
        ) or {}

        if provenance.get(
            "candidate_id"
        ) == candidate_id:
            return observation[
                "id"
            ]

    return None


def import_candidate(
    store: EventStore,
    payload: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    kwargs = build_observation_kwargs(
        payload,
        candidate,
    )

    candidate_id = kwargs[
        "provenance"
    ][
        "candidate_id"
    ]

    existing_id = (
        find_existing_candidate_observation_id(
            store,
            source_image_id=kwargs[
                "source_image_id"
            ],
            processing_version=kwargs[
                "processing_version"
            ],
            candidate_id=candidate_id,
        )
    )

    if existing_id is not None:
        return {
            "created": False,
            "observation_id": (
                existing_id
            ),
            "candidate_id": (
                candidate_id
            ),
            "source_image_id": (
                kwargs[
                    "source_image_id"
                ]
            ),
        }

    observation_id = (
        store.create_satellite_observation(
            **kwargs
        )
    )

    return {
        "created": True,
        "observation_id": (
            observation_id
        ),
        "candidate_id": (
            candidate_id
        ),
        "source_image_id": (
            kwargs[
                "source_image_id"
            ]
        ),
    }


def import_candidate_payload(
    store: EventStore,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    validate_candidate_payload(
        payload
    )

    results = []

    for candidate in payload[
        "candidates"
    ]:
        results.append(
            import_candidate(
                store,
                payload,
                candidate,
            )
        )

    return results


def import_candidate_file(
    store: EventStore,
    path: str | Path,
) -> list[dict[str, Any]]:
    payload = load_candidate_payload(
        path
    )

    return import_candidate_payload(
        store,
        payload,
    )
