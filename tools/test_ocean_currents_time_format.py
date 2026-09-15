from datetime import datetime, timezone

import numpy as np

from agents.ocean_data.copernicus_currents import (
    _iso_datetime,
)


def test_numpy_datetime64_is_rendered_as_iso_utc():
    value = np.datetime64(
        "2026-09-15T07:00:00.000000000"
    )

    assert (
        _iso_datetime(value)
        == "2026-09-15T07:00:00+00:00"
    )


def test_python_datetime_is_rendered_as_iso_utc():
    value = datetime(
        2026,
        9,
        15,
        10,
        0,
        tzinfo=timezone.utc,
    )

    assert (
        _iso_datetime(value)
        == "2026-09-15T10:00:00+00:00"
    )
