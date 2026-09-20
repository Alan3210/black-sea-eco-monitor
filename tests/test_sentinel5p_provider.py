from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.services.sentinel5p_provider import (
    DEFAULT_BLACK_SEA_BBOX,
    PROCESS_URL,
    Sentinel5PError,
    Sentinel5PProvider,
    build_process_request,
    product_info,
    satellite_semantics,
)


class FakeResponse:
    def __init__(
        self,
        *,
        status_code=200,
        json_data=None,
        content=b"",
        text="",
    ):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.content = content
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_data


class FakeSession:
    def __init__(self):
        self.calls = []
        self.token_calls = 0
        self.process_calls = 0

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if "openid-connect/token" in url:
            self.token_calls += 1
            return FakeResponse(
                json_data={
                    "access_token": "token-123",
                    "expires_in": 3600,
                }
            )
        if url == PROCESS_URL:
            self.process_calls += 1
            return FakeResponse(
                content=b"II*\x00FAKE_TIFF_CONTENT",
            )
        raise AssertionError(url)


def test_product_semantics_are_satellite_not_surface():
    semantics = satellite_semantics("no2")
    assert semantics["kind"] == "satellite_observation"
    assert semantics["observation"] is True
    assert semantics["model_forecast"] is False
    assert semantics["station_measurement"] is False
    assert semantics["surface_concentration"] is False
    assert product_info("no2")["units"] == "mol/m^2"


def test_no2_uses_qa_75_and_nearest():
    request = build_process_request(
        product="no2",
        start="2026-09-19T00:00:00Z",
        end="2026-09-19T23:59:00Z",
    )
    item = request["input"]["data"][0]
    assert item["type"] == "sentinel-5p-l2"
    assert item["processing"]["minQa"] == 75
    assert item["processing"]["upsampling"] == "NEAREST"
    assert request["input"]["bounds"]["bbox"] == list(DEFAULT_BLACK_SEA_BBOX)
    assert '"NO2"' in request["evalscript"]
    assert "dataMask" in request["evalscript"]
    assert "FLOAT32" in request["evalscript"]


def test_other_products_default_to_qa_50():
    request = build_process_request(
        product="so2",
        start="2026-09-19T00:00:00Z",
        end="2026-09-19T12:00:00Z",
    )
    assert request["input"]["data"][0]["processing"]["minQa"] == 50


def test_rejects_time_window_longer_than_24_hours():
    with pytest.raises(ValueError, match="24 hours"):
        build_process_request(
            product="co",
            start="2026-09-18T00:00:00Z",
            end="2026-09-19T00:00:01Z",
        )


def test_oauth_token_is_reused(tmp_path):
    session = FakeSession()
    provider = Sentinel5PProvider(
        client_id="id",
        client_secret="secret",
        cache_dir=tmp_path,
        session=session,
    )
    first = provider._get_token()
    second = provider._get_token()
    assert first == second == "token-123"
    assert session.token_calls == 1


def test_fetch_geotiff_and_cache_hit(tmp_path):
    session = FakeSession()
    provider = Sentinel5PProvider(
        client_id="id",
        client_secret="secret",
        cache_dir=tmp_path,
        session=session,
    )

    kwargs = dict(
        product="no2",
        start=datetime(2026, 9, 19, 0, 0, tzinfo=timezone.utc),
        end=datetime(2026, 9, 19, 23, 0, tzinfo=timezone.utc),
        timeliness="NRTI",
    )

    first = provider.fetch_geotiff(**kwargs)
    assert first.cache_hit is False
    assert first.path.exists()
    assert first.metadata_path.exists()
    assert first.metadata["band"] == "NO2"
    assert first.metadata["timeliness"] == "NRTI"
    assert first.metadata["min_qa"] == 75
    assert session.token_calls == 1
    assert session.process_calls == 1

    second = provider.fetch_geotiff(**kwargs)
    assert second.cache_hit is True
    assert second.path == first.path
    assert session.process_calls == 1


def test_missing_credentials_fails_before_network(tmp_path):
    provider = Sentinel5PProvider(
        client_id=None,
        client_secret=None,
        cache_dir=tmp_path,
        session=FakeSession(),
    )
    provider.client_id = None
    provider.client_secret = None
    with pytest.raises(Sentinel5PError, match="Missing CDSE"):
        provider._get_token()
