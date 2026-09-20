from __future__ import annotations

from dataclasses import dataclass

from backend.services.ground_station_source_registry import (
    primary_black_sea_station_source,
)
from tools.air1_6a_ground_station_source_probe import probe_eea


@dataclass
class FakeResponse:
    payload: object
    status_code: int = 200
    url: str = "https://example.test"

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError(self.status_code)

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self):
        self.posts = []

    def get(self, url, **kwargs):
        assert url.endswith("/Country")
        return FakeResponse(
            [
                {"countryCode": "BG", "countryName": "Bulgaria"},
                {"countryCode": "RO", "countryName": "Romania"},
                {"countryCode": "PL", "countryName": "Poland"},
            ]
        )

    def post(self, url, json=None, **kwargs):
        self.posts.append((url, json))
        return FakeResponse(
            {
                "numberFiles": 12,
                "size": 123456,
            }
        )


def test_primary_eea_scope_is_bulgaria_and_romania():
    assert primary_black_sea_station_source("BG") == "eea"
    assert primary_black_sea_station_source("RO") == "eea"
    assert primary_black_sea_station_source("TR") is None
    assert primary_black_sea_station_source("GE") is None


def test_eea_probe_confirms_expected_black_sea_scope():
    session = FakeSession()
    result = probe_eea(
        session=session,
        include_summary=True,
    )

    assert result["black_sea"]["supported"] == ["BG", "RO"]
    assert result["black_sea"]["not_in_current_country_endpoint"] == [
        "GE",
        "RU",
        "TR",
        "UA",
    ]
    assert result["black_sea"]["unexpected_present"] == []
    assert result["usable_for_primary_black_sea_station_layer"] is True


def test_eea_probe_uses_e2a_dataset_and_hourly_summary():
    session = FakeSession()
    probe_eea(
        session=session,
        include_summary=True,
    )

    assert len(session.posts) == 2
    for url, payload in session.posts:
        assert url.endswith("/DownloadSummary")
        assert payload["dataset"] == 1
        assert payload["aggregationType"] == "hour"
        assert payload["pollutants"] == [
            "PM2.5",
            "PM10",
            "NO2",
            "O3",
            "SO2",
            "CO",
        ]
