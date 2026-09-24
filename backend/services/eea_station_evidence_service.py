from __future__ import annotations

from backend.services.eea_station_fusion import (
    fuse_eea_station_observation,
)


def build_eea_station_observations(
    metadata_rows: list[dict],
    measurements: list[dict],
):
    metadata_index = {}

    for row in metadata_rows:
        key = row.get("AssessmentMethodId")
        if key:
            metadata_index[key] = row

    result = []

    for measurement in measurements:
        samplingpoint = measurement.get("samplingpoint", "")
        normalized = samplingpoint.split("/", 1)[-1]

        metadata = metadata_index.get(normalized)

        if metadata is None:
            continue

        result.append(
            fuse_eea_station_observation(
                metadata,
                measurement,
            )
        )

    return result
