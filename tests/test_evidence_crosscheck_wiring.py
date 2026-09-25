from backend.services.evidence_crosscheck_api_service import (
    get_evidence_crosscheck,
)


def test_evidence_crosscheck_wiring():
    result = get_evidence_crosscheck()

    assert result["status"] == "wired"
