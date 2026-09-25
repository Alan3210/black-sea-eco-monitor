from backend.services.eea_station_refresh_pipeline import refresh_eea_station_data

def test_refresh_pipeline_contract():
    result = refresh_eea_station_data(
        discovered_urls=["a"],
        downloaded_files=["a"],
        observations=[{"station_id":"1"}],
    )
    assert result["status"] == "success"
    assert result["stations_count"] == 1
