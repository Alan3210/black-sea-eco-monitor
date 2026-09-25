from backend.schemas.evidence_crosscheck import EvidenceCrosscheck
from backend.services.cams_evidence_adapter import (
    cams_to_evidence_record,
    station_to_evidence_record,
)
from backend.services.sentinel_evidence_adapter import (
    sentinel_to_evidence_record,
)


def build_triple_evidence_crosscheck(
    station,
    cams,
    sentinel,
):
    station_record = station_to_evidence_record(station)
    cams_record = cams_to_evidence_record(cams)
    sentinel_record = sentinel_to_evidence_record(sentinel)

    return EvidenceCrosscheck(
        position=station_record.position,
        observed_at=station_record.observed_at,
        sources=[
            station_record,
            cams_record,
            sentinel_record,
        ],
    )
