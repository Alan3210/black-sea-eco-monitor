from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import xarray as xr

from backend.services.ecmwf_weather_provider import (
    EcmwfOpenDataWeatherProvider,
    WeatherTimeUnavailable,
)


RUN = datetime(2026, 9, 18, 18, tzinfo=timezone.utc)


def make_dataset_loader():
    latitudes = [44.0, 45.0]
    longitudes = [37.0, 38.0]

    def loader(path: Path):
        name = path.name

        if name.startswith("wind_"):
            dataset = xr.Dataset(
                {
                    "u10": (
                        ("latitude", "longitude"),
                        np.full((2, 2), 3.0),
                    ),
                    "v10": (
                        ("latitude", "longitude"),
                        np.full((2, 2), 4.0),
                    ),
                },
                coords={
                    "latitude": latitudes,
                    "longitude": longitudes,
                },
            )
            return [dataset]

        if "step003" in name:
            tp = 0.003
        elif "step006" in name:
            tp = 0.006
        else:
            tp = 0.0

        dataset = xr.Dataset(
            {
                "tp": (
                    ("latitude", "longitude"),
                    np.full((2, 2), tp),
                )
            },
            coords={
                "latitude": latitudes,
                "longitude": longitudes,
            },
        )
        return [dataset]

    return loader


class FakeClient:
    def __init__(self, source, retrieve_log, *, fail=False):
        self.source = source
        self.retrieve_log = retrieve_log
        self.fail = fail

    def latest(self, **kwargs):
        if self.fail:
            raise RuntimeError("mirror unavailable")
        return RUN

    def retrieve(self, **kwargs):
        if self.fail:
            raise RuntimeError("mirror unavailable")

        target = Path(kwargs["target"])
        target.write_bytes(b"fake-grib")
        self.retrieve_log.append(
            (
                self.source,
                kwargs["step"],
                tuple(kwargs["param"]),
            )
        )
        return SimpleNamespace(datetime=RUN.replace(tzinfo=None))


def provider(tmp_path, *, fail_google=False):
    retrieve_log = []

    def factory(source):
        return FakeClient(
            source,
            retrieve_log,
            fail=(source == "google" and fail_google),
        )

    instance = EcmwfOpenDataWeatherProvider(
        cache_dir=tmp_path,
        sources=("google", "azure"),
        client_factory=factory,
        dataset_loader=make_dataset_loader(),
        now_fn=lambda: datetime(
            2026,
            9,
            19,
            0,
            tzinfo=timezone.utc,
        ),
    )
    return instance, retrieve_log


def test_step_schedule_for_18z_run():
    steps = EcmwfOpenDataWeatherProvider._steps_for_run(RUN)
    assert steps[0] == 0
    assert steps[-1] == 90
    assert 3 in steps
    assert 90 in steps


def test_step_schedule_for_00z_run_extends_to_240h():
    run = datetime(2026, 9, 19, 0, tzinfo=timezone.utc)
    steps = EcmwfOpenDataWeatherProvider._steps_for_run(run)
    assert 144 in steps
    assert 150 in steps
    assert 240 in steps
    assert 147 not in steps


def test_select_step_snaps_forward():
    step = EcmwfOpenDataWeatherProvider._select_step(
        run=RUN,
        requested_valid_time=datetime(
            2026,
            9,
            18,
            23,
            10,
            tzinfo=timezone.utc,
        ),
        now=RUN,
    )
    assert step == 6


def test_select_step_rejects_outside_horizon():
    with pytest.raises(WeatherTimeUnavailable):
        EcmwfOpenDataWeatherProvider._select_step(
            run=RUN,
            requested_valid_time=RUN.replace(
                day=23,
            ),
            now=RUN,
        )


def test_provider_normalizes_point_weather(tmp_path):
    instance, retrieve_log = provider(tmp_path)

    point = instance.get_point(
        latitude=44.5,
        longitude=37.5,
        valid_time=datetime(
            2026,
            9,
            19,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert point.wind_u_10m_ms == pytest.approx(3.0)
    assert point.wind_v_10m_ms == pytest.approx(4.0)
    assert point.wind_speed_10m_ms == pytest.approx(5.0)
    assert point.wind_from_direction_deg == pytest.approx(
        216.86989764584402
    )

    assert point.precipitation_accumulation_mm == pytest.approx(6.0)
    assert point.precipitation_rate_mm_h == pytest.approx(1.0)
    assert point.precipitation_interval_start == (
        RUN.replace(tzinfo=timezone.utc)
        .replace(hour=21)
    )
    assert point.provenance.forecast_reference_time == RUN
    assert point.provenance.valid_time == datetime(
        2026,
        9,
        19,
        0,
        tzinfo=timezone.utc,
    )
    assert point.provenance.source_uri == "google"
    assert point.provenance.fallback_used is False

    assert ("google", 6, ("10u", "10v")) in retrieve_log
    assert ("google", 6, ("tp",)) in retrieve_log
    assert ("google", 3, ("tp",)) in retrieve_log


def test_provider_uses_mirror_fallback(tmp_path):
    instance, _ = provider(
        tmp_path,
        fail_google=True,
    )

    point = instance.get_point(
        latitude=44.5,
        longitude=37.5,
        valid_time=datetime(
            2026,
            9,
            19,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert point.provenance.source_uri == "azure"
    assert point.provenance.fallback_used is True
    assert "provider_mirror_fallback" in (
        point.provenance.quality_flags
    )


def test_provider_reuses_cached_assets(tmp_path):
    instance, retrieve_log = provider(tmp_path)

    kwargs = {
        "latitude": 44.5,
        "longitude": 37.5,
        "valid_time": datetime(
            2026,
            9,
            19,
            0,
            tzinfo=timezone.utc,
        ),
    }

    instance.get_point(**kwargs)
    first_count = len(retrieve_log)

    instance.get_point(**kwargs)
    assert len(retrieve_log) == first_count
