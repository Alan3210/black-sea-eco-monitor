from backend.schemas.evidence_crosscheck import EvidenceCrosscheck
from backend.services.cams_evidence_adapter import (
    cams_to_evidence_record,
    station_to_evidence_record,
)


def build_station_cams_crosscheck(station, cams):
    station_record = station_to_evidence_record(station)
    cams_record = cams_to_evidence_record(cams)

    return EvidenceCrosscheck(
        position=station_record.position,
        observed_at=station_record.observed_at,
        sources=[
            station_record,
            cams_record,
        ],
    )
