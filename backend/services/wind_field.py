from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any

import numpy as np

from agents.ocean_data.copernicus_currents import (
    MAX_LATITUDE,
    MAX_LONGITUDE,
    MIN_LATITUDE,
    MIN_LONGITUDE,
)
from backend.services.ecmwf_wind_forcing import (
    EcmwfWindForcingBuilder,
)


DEFAULT_WIND_FIELD_STRIDE = 2
MIN_WIND_FIELD_STRIDE = 1
MAX_WIND_FIELD_STRIDE = 8

BLACK_SEA_WIND_BBOX = {
    "west": float(MIN_LONGITUDE),
    "south": float(MIN_LATITUDE),
    "east": float(MAX_LONGITUDE),
    "north": float(MAX_LATITUDE),
}


def normalize_wind_field_time(
    value: str | datetime | None,
) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)

    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()

        if not text:
            return datetime.now(timezone.utc)

        try:
            parsed = datetime.fromisoformat(
                text.replace("Z", "+00:00")
            )
        except ValueError as exc:
            raise ValueError(
                "at must be an ISO 8601 datetime"
            ) from exc

    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.astimezone(
        timezone.utc
    )


def validate_wind_field_stride(
    value: int,
) -> int:
    stride = int(value)

    if not (
        MIN_WIND_FIELD_STRIDE
        <= stride
        <= MAX_WIND_FIELD_STRIDE
    ):
        raise ValueError(
            "stride must be between "
            f"{MIN_WIND_FIELD_STRIDE} and "
            f"{MAX_WIND_FIELD_STRIDE}"
        )

    return stride


def wind_direction_to_deg(
    u_ms: float,
    v_ms: float,
) -> float:
    return (
        math.degrees(
            math.atan2(
                float(u_ms),
                float(v_ms),
            )
        )
        + 360.0
    ) % 360.0


def wind_direction_from_deg(
    u_ms: float,
    v_ms: float,
) -> float:
    return (
        wind_direction_to_deg(
            u_ms,
            v_ms,
        )
        + 180.0
    ) % 360.0


def _iso_utc(value: datetime) -> str:
    return value.astimezone(
        timezone.utc
    ).isoformat()


def _time_coord_iso(
    value: np.datetime64,
) -> str:
    value_ns = np.datetime64(
        value,
        "ns",
    ).astype("int64")

    return datetime.fromtimestamp(
        value_ns / 1_000_000_000,
        tz=timezone.utc,
    ).isoformat()


class EcmwfWindFieldService:
    """
    Map-ready ECMWF IFS 10 m wind field.

    Uses the same WEATHER-1.3A forcing builder as OceanDrift and
    interpolates u10/v10 linearly to the requested valid time.
    """

    def __init__(
        self,
        *,
        builder: EcmwfWindForcingBuilder | None = None,
    ):
        self.builder = (
            builder
            if builder is not None
            else EcmwfWindForcingBuilder()
        )

    def get_field(
        self,
        *,
        at: str | datetime | None = None,
        stride: int = DEFAULT_WIND_FIELD_STRIDE,
        bbox: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        target_time = normalize_wind_field_time(
            at
        )
        stride = validate_wind_field_stride(
            stride
        )
        requested_bbox = dict(
            bbox or BLACK_SEA_WIND_BBOX
        )

        forcing = self.builder.build(
            start_time=target_time,
            hours=1,
            bbox=requested_bbox,
        )

        dataset = forcing.dataset

        # Normalize the temporal coordinate explicitly. Some xarray
        # versions can return NaNs when interpolating datetime64[s]
        # coordinates against datetime64[ns] query values.
        dataset = dataset.assign_coords(
            time=np.asarray(
                dataset["time"].values,
            ).astype("datetime64[ns]")
        )

        target_np = np.datetime64(
            target_time.replace(
                tzinfo=None
            ),
            "ns",
        )

        start_np = np.datetime64(
            dataset["time"].values[0],
            "ns",
        )
        end_np = np.datetime64(
            dataset["time"].values[-1],
            "ns",
        )

        if (
            target_np < start_np
            or target_np > end_np
        ):
            raise ValueError(
                "requested time is outside the "
                "prepared ECMWF wind cube"
            )

        field = dataset[
            ["u10", "v10"]
        ].interp(
            time=target_np
        )

        latitudes = np.asarray(
            field["latitude"].values,
            dtype=float,
        )
        longitudes = np.asarray(
            field["longitude"].values,
            dtype=float,
        )
        u_values = np.asarray(
            field["u10"].values,
            dtype=float,
        )
        v_values = np.asarray(
            field["v10"].values,
            dtype=float,
        )

        vectors: list[dict[str, float]] = []
        speeds: list[float] = []

        for lat_index in range(
            0,
            len(latitudes),
            stride,
        ):
            for lon_index in range(
                0,
                len(longitudes),
                stride,
            ):
                u_ms = float(
                    u_values[
                        lat_index,
                        lon_index,
                    ]
                )
                v_ms = float(
                    v_values[
                        lat_index,
                        lon_index,
                    ]
                )

                if not (
                    math.isfinite(u_ms)
                    and math.isfinite(v_ms)
                ):
                    continue

                speed_ms = math.hypot(
                    u_ms,
                    v_ms,
                )
                direction_to = (
                    wind_direction_to_deg(
                        u_ms,
                        v_ms,
                    )
                )
                direction_from = (
                    wind_direction_from_deg(
                        u_ms,
                        v_ms,
                    )
                )

                speeds.append(
                    speed_ms
                )

                vectors.append(
                    {
                        "latitude": round(
                            float(
                                latitudes[
                                    lat_index
                                ]
                            ),
                            6,
                        ),
                        "longitude": round(
                            float(
                                longitudes[
                                    lon_index
                                ]
                            ),
                            6,
                        ),
                        "u_ms": round(
                            u_ms,
                            6,
                        ),
                        "v_ms": round(
                            v_ms,
                            6,
                        ),
                        "speed_ms": round(
                            speed_ms,
                            6,
                        ),
                        "direction_from_deg": round(
                            direction_from,
                            3,
                        ),
                        "direction_to_deg": round(
                            direction_to,
                            3,
                        ),
                    }
                )

        stats = {
            "min_speed_ms": None,
            "mean_speed_ms": None,
            "max_speed_ms": None,
        }

        if speeds:
            stats = {
                "min_speed_ms": round(
                    min(speeds),
                    6,
                ),
                "mean_speed_ms": round(
                    sum(speeds)
                    / len(speeds),
                    6,
                ),
                "max_speed_ms": round(
                    max(speeds),
                    6,
                ),
            }

        provenance = forcing.provenance()

        return {
            "provider": "ecmwf",
            "model": "ifs",
            "product": provenance.get(
                "product",
                "open-data-0p25",
            ),
            "height_m": 10,
            "requested_time": _iso_utc(
                target_time
            ),
            "valid_time": _iso_utc(
                target_time
            ),
            "forecast_reference_time": provenance[
                "forecast_reference_time"
            ],
            "retrieved_at": provenance[
                "retrieved_at"
            ],
            "sources": list(
                provenance.get(
                    "sources",
                    [],
                )
            ),
            "fallback_used": bool(
                provenance.get(
                    "fallback_used",
                    False,
                )
            ),
            "temporal_interpolation": (
                "linear_between_native_ifs_steps"
            ),
            "direction_convention": {
                "direction_from_deg": (
                    "meteorological FROM, "
                    "clockwise from true north"
                ),
                "direction_to_deg": (
                    "motion TO, clockwise "
                    "from true north"
                ),
            },
            "bbox": {
                key: float(value)
                for key, value
                in requested_bbox.items()
            },
            "stride": stride,
            "native_grid_shape": {
                "latitude": int(
                    len(latitudes)
                ),
                "longitude": int(
                    len(longitudes)
                ),
            },
            "vector_count": len(
                vectors
            ),
            "speed_stats": stats,
            "vectors": vectors,
            "forcing_steps": list(
                forcing.steps
            ),
            "forcing_cube_start": _time_coord_iso(
                dataset["time"].values[0]
            ),
            "forcing_cube_end": _time_coord_iso(
                dataset["time"].values[-1]
            ),
        }
