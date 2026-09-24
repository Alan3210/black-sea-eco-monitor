from __future__ import annotations

from backend.services.eea_station_evidence_service import (
    build_eea_station_observations,
)


def get_eea_station_observations(
    metadata_rows: list[dict],
    measurements: list[dict],
):
    return build_eea_station_observations(
        metadata_rows,
        measurements,
    )
