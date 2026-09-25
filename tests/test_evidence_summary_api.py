from backend.api.evidence_summary import evidence_summary


def test_evidence_summary_contract():
    result = evidence_summary()

    assert "sources" in result
    assert "quality" in result
    assert result["sources"]["station_measurements"]["available"] is True
