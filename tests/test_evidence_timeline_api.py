from backend.api.evidence_timeline import evidence_timeline


def test_evidence_timeline_contract():
    result = evidence_timeline()

    assert result["pollutant"] == "PM10"
    assert len(result["series"]) == 3
    assert result["series"][0]["source"] == "EEA"
