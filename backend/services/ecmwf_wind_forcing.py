from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import numpy as np
import xarray as xr

from backend.services.ecmwf_weather_provider import (
    CachedAsset,
    EcmwfOpenDataWeatherProvider,
    WeatherProviderError,
    WeatherSourceUnavailable,
    WeatherTimeUnavailable,
)
from backend.services.weather_math import longitude_for_dataset


@dataclass
class EcmwfWindForcingCube:
    dataset: xr.Dataset
    forecast_reference_time: datetime
    start_time: datetime
    end_time: datetime
    steps: tuple[int, ...]
    sources: tuple[str, ...]
    fallback_used: bool
    retrieved_at: datetime
    bbox: dict[str, float]

    def provenance(self) -> dict:
        return {
            "provider": "ecmwf",
            "model": "ifs",
            "product": "open-data-0p25",
            "forecast_reference_time": (
                self.forecast_reference_time.isoformat()
            ),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "steps": list(self.steps),
            "sources": list(self.sources),
            "fallback_used": self.fallback_used,
            "retrieved_at": self.retrieved_at.isoformat(),
            "bbox": dict(self.bbox),
            "variables": ["u10", "v10"],
            "opendrift_variables": ["x_wind", "y_wind"],
            "temporal_interpolation": "OpenDrift reader interpolation",
        }


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _numpy_datetime_to_utc(value) -> datetime:
    raw = np.asarray(value).reshape(-1)[0]
    value_ns = np.datetime64(raw, "ns").astype("int64")
    return datetime.fromtimestamp(
        value_ns / 1_000_000_000,
        tz=timezone.utc,
    )


def required_wind_steps(
    *,
    run: datetime,
    start_time: datetime,
    end_time: datetime,
) -> tuple[int, ...]:
    """
    Return forecast steps bracketing the full simulation interval.

    The first slice is at or before the simulation start and the final slice
    is at or after the simulation end, allowing the OpenDrift reader to
    interpolate wind in time between native IFS forecast steps.
    """
    run_utc = _utc(run)
    start = _utc(start_time)
    end = _utc(end_time)

    if end <= start:
        raise ValueError("end_time must be after start_time")

    schedule = EcmwfOpenDataWeatherProvider._steps_for_run(run_utc)
    start_hours = (start - run_utc).total_seconds() / 3600.0
    end_hours = (end - run_utc).total_seconds() / 3600.0

    if start_hours < 0.0:
        raise WeatherTimeUnavailable(
            "simulation start precedes the selected ECMWF forecast run"
        )

    before = [
        step
        for step in schedule
        if step <= start_hours + 1e-9
    ]
    after = [
        step
        for step in schedule
        if step >= end_hours - 1e-9
    ]

    if not before or not after:
        raise WeatherTimeUnavailable(
            "simulation interval is outside the available "
            "ECMWF forecast horizon"
        )

    first = before[-1]
    last = after[0]

    return tuple(
        step
        for step in schedule
        if first <= step <= last
    )


class EcmwfWindForcingBuilder:
    """
    Build a cropped time × latitude × longitude IFS 10 m wind cube.

    The builder reuses WEATHER-1.1 mirror failover and deterministic GRIB
    cache. It does not modify currents or run OpenDrift itself.
    """

    def __init__(
        self,
        *,
        provider: EcmwfOpenDataWeatherProvider | None = None,
    ):
        self.provider = (
            provider
            if provider is not None
            else EcmwfOpenDataWeatherProvider()
        )

    def _latest_run(self) -> tuple[datetime, str]:
        errors: list[str] = []

        for source in self.provider.sources:
            try:
                client = self.provider._client(source)
                run = client.latest(
                    type="fc",
                    step=3,
                    param="10u",
                )
                return _utc(run), source
            except Exception as exc:
                errors.append(
                    f"{source}: {type(exc).__name__}: {exc}"
                )

        raise WeatherSourceUnavailable(
            "unable to resolve latest ECMWF run: "
            + " | ".join(errors)
        )

    def _source_order(
        self,
        preferred_source: str,
    ) -> tuple[str, ...]:
        return (
            preferred_source,
            *(
                source
                for source in self.provider.sources
                if source != preferred_source
            ),
        )

    def _retrieve_wind_asset(
        self,
        *,
        run: datetime,
        step: int,
        preferred_source: str,
    ) -> CachedAsset:
        errors: list[str] = []

        for source in self._source_order(preferred_source):
            try:
                client = self.provider._client(source)
                return self.provider._retrieve_asset(
                    client=client,
                    source=source,
                    run=run,
                    step=step,
                    params=["10u", "10v"],
                    kind="wind",
                )
            except Exception as exc:
                errors.append(
                    f"{source}: {type(exc).__name__}: {exc}"
                )

        raise WeatherSourceUnavailable(
            f"all ECMWF mirrors failed for wind step {step}: "
            + " | ".join(errors)
        )

    @staticmethod
    def _wind_dataset(datasets: list[xr.Dataset]) -> xr.Dataset:
        for dataset in datasets:
            if (
                "u10" in dataset.data_vars
                and "v10" in dataset.data_vars
            ):
                return dataset
        raise WeatherProviderError(
            "ECMWF wind GRIB does not contain both u10 and v10"
        )

    @staticmethod
    def _crop_longitude(
        dataset: xr.Dataset,
        *,
        west: float,
        east: float,
    ) -> xr.Dataset:
        uses_360 = (
            float(dataset["longitude"].max()) > 180.0
        )
        west_ds = longitude_for_dataset(
            west,
            dataset_uses_360=uses_360,
        )
        east_ds = longitude_for_dataset(
            east,
            dataset_uses_360=uses_360,
        )

        longitude = dataset["longitude"]
        lon_min = float(longitude.min())
        lon_max = float(longitude.max())

        if west_ds <= east_ds:
            return dataset.sel(
                longitude=slice(west_ds, east_ds)
            )

        left = dataset.sel(
            longitude=slice(west_ds, lon_max)
        )
        right = dataset.sel(
            longitude=slice(lon_min, east_ds)
        )
        return xr.concat(
            [left, right],
            dim="longitude",
        )

    @classmethod
    def _normalize_slice(
        cls,
        dataset: xr.Dataset,
        *,
        bbox: dict[str, float],
    ) -> tuple[xr.Dataset, datetime]:
        if "valid_time" not in dataset.coords:
            raise WeatherProviderError(
                "ECMWF wind dataset has no valid_time coordinate"
            )

        valid_time = _numpy_datetime_to_utc(
            dataset["valid_time"].values
        )

        wind = dataset[["u10", "v10"]]

        drop_coords = [
            name
            for name in (
                "time",
                "step",
                "heightAboveGround",
                "valid_time",
            )
            if name in wind.coords
        ]
        wind = wind.drop_vars(
            drop_coords,
            errors="ignore",
        )

        if (
            "latitude" not in wind.coords
            or "longitude" not in wind.coords
        ):
            raise WeatherProviderError(
                "ECMWF wind dataset requires latitude/longitude coordinates"
            )

        wind = wind.sortby("latitude").sortby("longitude")

        wind = wind.sel(
            latitude=slice(
                float(bbox["south"]),
                float(bbox["north"]),
            ),
        )
        wind = cls._crop_longitude(
            wind,
            west=float(bbox["west"]),
            east=float(bbox["east"]),
        )

        if (
            wind.sizes.get("latitude", 0) == 0
            or wind.sizes.get("longitude", 0) == 0
        ):
            raise WeatherProviderError(
                "requested forcing bbox does not intersect ECMWF grid"
            )

        # OpenDrift 1.14.x generic reader requires a true 1-D time axis.
        wind = wind.expand_dims(
            time=[valid_time.replace(tzinfo=None)]
        )

        return wind, valid_time

    def build(
        self,
        *,
        start_time: datetime,
        hours: int,
        bbox: dict[str, float],
    ) -> EcmwfWindForcingCube:
        if hours <= 0:
            raise ValueError("hours must be positive")

        start = _utc(start_time)
        end = start + timedelta(hours=int(hours))

        run, preferred_source = self._latest_run()
        steps = required_wind_steps(
            run=run,
            start_time=start,
            end_time=end,
        )

        slices: list[xr.Dataset] = []
        sources: set[str] = set()
        retrieved_times: list[datetime] = []
        actual_times: list[datetime] = []

        for step in steps:
            asset = self._retrieve_wind_asset(
                run=run,
                step=step,
                preferred_source=preferred_source,
            )
            datasets = self.provider._dataset_loader(
                asset.path
            )
            dataset = self._wind_dataset(datasets)
            normalized, valid_time = self._normalize_slice(
                dataset,
                bbox=bbox,
            )

            slices.append(normalized)
            sources.add(asset.source)
            retrieved_times.append(asset.retrieved_at)
            actual_times.append(valid_time)

        cube = xr.concat(
            slices,
            dim="time",
            data_vars="minimal",
            coords="minimal",
            compat="override",
            join="exact",
        ).sortby("time")

        # Make the cube explicit and compact before handing it to OpenDrift.
        cube = cube[["u10", "v10"]]
        cube.attrs.update(
            {
                "provider": "ecmwf",
                "model": self.provider.model,
                "product": f"open-data-{self.provider.resolution}",
                "forecast_reference_time": run.isoformat(),
            }
        )

        source_tuple = tuple(sorted(sources))
        fallback_used = any(
            source != self.provider.sources[0]
            for source in source_tuple
        )

        return EcmwfWindForcingCube(
            dataset=cube,
            forecast_reference_time=run,
            start_time=start,
            end_time=end,
            steps=steps,
            sources=source_tuple,
            fallback_used=fallback_used,
            retrieved_at=max(retrieved_times),
            bbox={
                key: float(value)
                for key, value in bbox.items()
            },
        )


def build_opendrift_wind_reader(
    forcing: EcmwfWindForcingCube,
):
    try:
        from opendrift.readers import (
            reader_netCDF_CF_generic,
        )
    except ImportError as exc:
        raise WeatherProviderError(
            "OpenDrift is not installed"
        ) from exc

    return reader_netCDF_CF_generic.Reader(
        forcing.dataset,
        name="ECMWF IFS 10 m wind",
        standard_name_mapping={
            "u10": "x_wind",
            "v10": "y_wind",
        },
    )
