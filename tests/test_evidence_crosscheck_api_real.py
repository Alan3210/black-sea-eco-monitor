from backend.api.evidence_crosscheck import evidence_crosscheck


def test_real_evidence_crosscheck_endpoint_contract():
    result = evidence_crosscheck()

    assert result["status"] == "wired"
    assert isinstance(result["sources"], list)
