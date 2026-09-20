from datetime import datetime, timezone
import json
from pathlib import Path
import zipfile
import pytest

from backend.services.cams_air_quality_provider import (
    CAMS_DATASET, CamsEuropeAirQualityProvider, CamsRequestError,
    build_cams_request, default_operational_run_date, normalize_area,
    normalize_pollutants, request_cache_key,
)

class FakeCdsClient:
    def __init__(self): self.calls = []
    def retrieve(self, dataset, request, target):
        self.calls.append((dataset, request, target))
        path = Path(target); path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("pm25.nc", b"synthetic-netcdf-placeholder")

def test_builds_current_ads_request_contract():
    request = build_cams_request(run_date="2026-09-19", lead_hours=[0,1,24,96], pollutants=["pm25","no2","o3"])
    assert request["model"] == ["ensemble"]
    assert request["level"] == ["0"]
    assert request["type"] == ["forecast"]
    assert request["time"] == ["00:00"]
    assert request["data_format"] == "netcdf_zip"
    assert request["variable"] == ["particulate_matter_2.5um", "nitrogen_dioxide", "ozone"]
    assert request["leadtime_hour"] == ["0","1","24","96"]

def test_rejects_out_of_domain_area():
    with pytest.raises(CamsRequestError): normalize_area([80,26,39,43])

def test_rejects_unknown_pollutant():
    with pytest.raises(CamsRequestError): normalize_pollutants(["pm25","magic_smoke"])

def test_cache_key_is_deterministic():
    a = build_cams_request(run_date="2026-09-19", lead_hours=[24,0,12], pollutants=["pm25","pm10"])
    b = build_cams_request(run_date="2026-09-19", lead_hours=[12,24,0], pollutants=["pm25","pm10"])
    assert request_cache_key(a) == request_cache_key(b)

def test_default_operational_run_uses_previous_day_before_cutoff():
    now = datetime(2026,9,20,8,0,tzinfo=timezone.utc)
    assert str(default_operational_run_date(now)) == "2026-09-19"

def test_provider_downloads_extracts_writes_provenance_and_reuses_cache(tmp_path):
    fake = FakeCdsClient()
    provider = CamsEuropeAirQualityProvider(cache_dir=tmp_path, client_factory=lambda: fake, now_factory=lambda: datetime(2026,9,19,12,34,tzinfo=timezone.utc))
    first = provider.retrieve(run_date="2026-09-19", lead_hours=[0,6,12], pollutants=["pm25","no2","dust"])
    assert first.cache_hit is False
    assert len(fake.calls) == 1 and fake.calls[0][0] == CAMS_DATASET
    assert Path(first.zip_path).exists()
    assert [Path(x).name for x in first.extracted_files] == ["pm25.nc"]
    meta = json.loads(Path(first.metadata_path).read_text(encoding="utf-8"))
    assert meta["model"] == "ensemble"
    assert meta["semantics"]["kind"] == "model_forecast"
    assert meta["semantics"]["observation"] is False
    assert meta["pollutant_metadata"]["dust"]["quality_status"] == "experimental"
    second = provider.retrieve(run_date="2026-09-19", lead_hours=[0,6,12], pollutants=["pm25","no2","dust"])
    assert second.cache_hit is True
    assert len(fake.calls) == 1
