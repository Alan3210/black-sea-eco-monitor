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
from backend.services.ecmwf_wind_forcing import (
    EcmwfWindForcingBuilder,
    required_wind_steps,
)


RUN = datetime(2026, 9, 19, 0, tzinfo=timezone.utc)


def test_required_steps_bracket_simulation_window():
    steps = required_wind_steps(
        run=RUN,
        start_time=datetime(
            2026, 9, 19, 7, tzinfo=timezone.utc
        ),
        end_time=datetime(
            2026, 9, 19, 19, tzinfo=timezone.utc
        ),
    )

    assert steps == (6, 9, 12, 15, 18, 21)


def test_required_steps_exact_boundaries():
    steps = required_wind_steps(
        run=RUN,
        start_time=datetime(
            2026, 9, 19, 9, tzinfo=timezone.utc
        ),
        end_time=datetime(
            2026, 9, 19, 18, tzinfo=timezone.utc
        ),
    )

    assert steps == (9, 12, 15, 18)


def test_required_steps_reject_start_before_run():
    with pytest.raises(WeatherTimeUnavailable):
        required_wind_steps(
            run=RUN,
            start_time=datetime(
                2026, 9, 18, 23, tzinfo=timezone.utc
            ),
            end_time=datetime(
                2026, 9, 19, 6, tzinfo=timezone.utc
            ),
        )


class FakeClient:
    def __init__(self, source, log, fail=False):
        self.source = source
        self.log = log
        self.fail = fail

    def latest(self, **kwargs):
        if self.fail:
            raise RuntimeError("mirror unavailable")
        return RUN

    def retrieve(self, **kwargs):
        if self.fail:
            raise RuntimeError("mirror unavailable")

        path = Path(kwargs["target"])
        path.write_bytes(b"fake-grib")
        self.log.append(
            (self.source, int(kwargs["step"]))
        )
        return SimpleNamespace(
            datetime=RUN.replace(tzinfo=None)
        )


def dataset_loader(path: Path):
    step = int(
        path.stem.split("step")[-1]
    )
    valid = np.datetime64(
        RUN.replace(tzinfo=None)
    ) + np.timedelta64(step, "h")

    latitudes = np.array(
        [46.0, 45.0, 44.0, 43.0],
    )
    longitudes = np.array(
        [36.0, 37.0, 38.0, 39.0],
    )

    return [
        xr.Dataset(
            {
                "u10": (
                    ("latitude", "longitude"),
                    np.full((4, 4), float(step)),
                ),
                "v10": (
                    ("latitude", "longitude"),
                    np.full((4, 4), -float(step)),
                ),
            },
            coords={
                "time": np.datetime64(
                    RUN.replace(tzinfo=None)
                ),
                "step": np.timedelta64(step, "h"),
                "heightAboveGround": 10.0,
                "valid_time": valid,
                "latitude": latitudes,
                "longitude": longitudes,
            },
        )
    ]


def make_builder(tmp_path, *, fail_google=False):
    log = []

    def factory(source):
        return FakeClient(
            source,
            log,
            fail=(
                source == "google"
                and fail_google
            ),
        )

    provider = EcmwfOpenDataWeatherProvider(
        cache_dir=tmp_path,
        sources=("google", "azure"),
        client_factory=factory,
        dataset_loader=dataset_loader,
        now_fn=lambda: datetime(
            2026, 9, 19, 7, tzinfo=timezone.utc
        ),
    )

    return EcmwfWindForcingBuilder(
        provider=provider,
    ), log


def test_builder_creates_cropped_time_cube(tmp_path):
    builder, log = make_builder(tmp_path)

    forcing = builder.build(
        start_time=datetime(
            2026, 9, 19, 7, tzinfo=timezone.utc
        ),
        hours=12,
        bbox={
            "west": 36.5,
            "east": 38.5,
            "south": 43.5,
            "north": 45.5,
        },
    )

    assert forcing.steps == (6, 9, 12, 15, 18, 21)
    assert forcing.dataset.sizes["time"] == 6
    assert forcing.dataset.sizes["latitude"] == 2
    assert forcing.dataset.sizes["longitude"] == 2
    assert list(forcing.dataset.data_vars) == [
        "u10",
        "v10",
    ]
    assert forcing.sources == ("google",)
    assert forcing.fallback_used is False
    assert log == [
        ("google", 6),
        ("google", 9),
        ("google", 12),
        ("google", 15),
        ("google", 18),
        ("google", 21),
    ]


def test_builder_time_axis_is_monotonic(tmp_path):
    builder, _ = make_builder(tmp_path)

    forcing = builder.build(
        start_time=datetime(
            2026, 9, 19, 9, tzinfo=timezone.utc
        ),
        hours=9,
        bbox={
            "west": 36.0,
            "east": 39.0,
            "south": 43.0,
            "north": 46.0,
        },
    )

    values = forcing.dataset["time"].values
    assert all(
        values[index] < values[index + 1]
        for index in range(len(values) - 1)
    )


def test_builder_records_mirror_fallback(tmp_path):
    builder, _ = make_builder(
        tmp_path,
        fail_google=True,
    )

    forcing = builder.build(
        start_time=datetime(
            2026, 9, 19, 7, tzinfo=timezone.utc
        ),
        hours=3,
        bbox={
            "west": 36.0,
            "east": 39.0,
            "south": 43.0,
            "north": 46.0,
        },
    )

    assert forcing.sources == ("azure",)
    assert forcing.fallback_used is True
    assert forcing.provenance()["opendrift_variables"] == [
        "x_wind",
        "y_wind",
    ]
