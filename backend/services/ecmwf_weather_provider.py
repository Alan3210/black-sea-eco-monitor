from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Callable, Iterable

import xarray as xr

from backend.schemas.weather import WeatherPoint, WeatherProvenance
from backend.services.weather_math import (
    deaccumulate_precipitation_mm,
    longitude_for_dataset,
    precipitation_m_to_mm,
    wind_from_direction_deg,
    wind_speed_ms,
)


DEFAULT_ECMWF_SOURCES = (
    "google",
    "azure",
    "aws",
    "ecmwf",
)


class WeatherProviderError(RuntimeError):
    pass


class WeatherSourceUnavailable(WeatherProviderError):
    pass


class WeatherTimeUnavailable(WeatherProviderError):
    pass


@dataclass(frozen=True)
class CachedAsset:
    path: Path
    source: str
    retrieved_at: datetime


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _default_now() -> datetime:
    return datetime.now(timezone.utc)


def _default_dataset_loader(path: Path) -> list[xr.Dataset]:
    import cfgrib

    return list(
        cfgrib.open_datasets(
            str(path),
            backend_kwargs={"indexpath": ""},
        )
    )


class EcmwfOpenDataWeatherProvider:
    """
    ECMWF IFS Open Data point-weather provider.

    WEATHER-1.1 responsibilities:
    - mirror failover;
    - deterministic GRIB cache;
    - exact forecast-run provenance;
    - native-grid spatial interpolation at a point;
    - u10/v10 normalization;
    - total-precipitation deaccumulation within one model run.

    It intentionally does NOT perform temporal interpolation and does not
    feed OpenDrift/OpenOil yet.
    """

    provider_name = "ecmwf"

    def __init__(
        self,
        *,
        cache_dir: str | Path = "data/cache/weather/ecmwf",
        sources: Iterable[str] = DEFAULT_ECMWF_SOURCES,
        model: str = "ifs",
        resolution: str = "0p25",
        client_factory: Callable[[str], object] | None = None,
        dataset_loader: Callable[[Path], list[xr.Dataset]] | None = None,
        now_fn: Callable[[], datetime] = _default_now,
    ):
        self.cache_dir = Path(cache_dir)
        self.sources = tuple(sources)
        if not self.sources:
            raise ValueError("at least one ECMWF source is required")

        self.model = model
        self.resolution = resolution
        self._client_factory = client_factory
        self._dataset_loader = (
            dataset_loader
            if dataset_loader is not None
            else _default_dataset_loader
        )
        self._now_fn = now_fn

    def _client(self, source: str):
        if self._client_factory is not None:
            return self._client_factory(source)

        from ecmwf.opendata import Client

        return Client(
            source=source,
            model=self.model,
            resol=self.resolution,
        )

    @staticmethod
    def _steps_for_run(run: datetime) -> list[int]:
        hour = _utc(run).hour

        if hour in (6, 18):
            return list(range(0, 91, 3))

        if hour in (0, 12):
            return (
                list(range(0, 145, 3))
                + list(range(150, 241, 6))
            )

        raise WeatherTimeUnavailable(
            f"unsupported IFS run hour: {hour:02d} UTC"
        )

    @classmethod
    def _select_step(
        cls,
        *,
        run: datetime,
        requested_valid_time: datetime | None,
        now: datetime,
    ) -> int:
        run_utc = _utc(run)
        target = (
            _utc(requested_valid_time)
            if requested_valid_time is not None
            else _utc(now)
        )

        steps = cls._steps_for_run(run_utc)

        # WEATHER-1.1 serves an operational forecast point, not an analysis
        # field. Prefer the first positive step when target <= run.
        minimum_step = 3
        candidate_steps = [
            step
            for step in steps
            if step >= minimum_step
        ]

        elapsed_hours = (
            target - run_utc
        ).total_seconds() / 3600.0

        for step in candidate_steps:
            if step + 1e-9 >= elapsed_hours:
                return step

        raise WeatherTimeUnavailable(
            "requested valid time is outside the available "
            "IFS Open Data forecast horizon"
        )

    @classmethod
    def _previous_step(
        cls,
        *,
        run: datetime,
        step: int,
    ) -> int:
        steps = cls._steps_for_run(run)
        earlier = [value for value in steps if value < step]
        if not earlier:
            return 0
        return earlier[-1]

    def _asset_path(
        self,
        *,
        run: datetime,
        step: int,
        kind: str,
    ) -> Path:
        run_utc = _utc(run)
        run_dir = (
            self.cache_dir
            / run_utc.strftime("%Y%m%d%H")
        )
        return run_dir / f"{kind}_step{step:03d}.grib2"

    @staticmethod
    def _metadata_path(path: Path) -> Path:
        return path.with_suffix(path.suffix + ".json")

    @staticmethod
    def _read_asset_metadata(path: Path) -> dict | None:
        meta_path = EcmwfOpenDataWeatherProvider._metadata_path(path)
        if not meta_path.exists():
            return None

        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    @staticmethod
    def _write_asset_metadata(
        path: Path,
        *,
        source: str,
        run: datetime,
        step: int,
        params: list[str],
        retrieved_at: datetime,
    ) -> None:
        meta_path = EcmwfOpenDataWeatherProvider._metadata_path(path)
        payload = {
            "source": source,
            "run": _utc(run).isoformat(),
            "step": step,
            "params": params,
            "retrieved_at": _utc(retrieved_at).isoformat(),
        }
        meta_path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    def _cached_asset(self, path: Path) -> CachedAsset | None:
        if not path.exists() or path.stat().st_size <= 0:
            return None

        metadata = self._read_asset_metadata(path)
        if not metadata:
            return None

        try:
            retrieved_at = datetime.fromisoformat(
                metadata["retrieved_at"]
            )
            source = str(metadata["source"])
        except Exception:
            return None

        return CachedAsset(
            path=path,
            source=source,
            retrieved_at=_utc(retrieved_at),
        )

    def _retrieve_asset(
        self,
        *,
        client,
        source: str,
        run: datetime,
        step: int,
        params: list[str],
        kind: str,
    ) -> CachedAsset:
        target = self._asset_path(
            run=run,
            step=step,
            kind=kind,
        )
        cached = self._cached_asset(target)
        if cached is not None:
            return cached

        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(target.suffix + ".part")
        partial.unlink(missing_ok=True)

        try:
            client.retrieve(
                date=_utc(run).replace(tzinfo=None),
                type="fc",
                step=step,
                param=params,
                target=str(partial),
            )
            if not partial.exists() or partial.stat().st_size <= 0:
                raise WeatherSourceUnavailable(
                    f"ECMWF source {source!r} returned an empty asset"
                )

            partial.replace(target)
            retrieved_at = _utc(self._now_fn())
            self._write_asset_metadata(
                target,
                source=source,
                run=run,
                step=step,
                params=params,
                retrieved_at=retrieved_at,
            )
            return CachedAsset(
                path=target,
                source=source,
                retrieved_at=retrieved_at,
            )
        finally:
            partial.unlink(missing_ok=True)

    @staticmethod
    def _dataset_uses_360(ds: xr.Dataset) -> bool:
        longitude = ds.coords.get("longitude")
        if longitude is None:
            raise WeatherProviderError(
                "ECMWF dataset has no longitude coordinate"
            )
        return float(longitude.max()) > 180.0

    @staticmethod
    def _find_dataset(
        datasets: list[xr.Dataset],
        variable: str,
    ) -> xr.Dataset:
        for dataset in datasets:
            if variable in dataset.data_vars:
                return dataset
        raise WeatherProviderError(
            f"GRIB asset does not contain variable {variable!r}"
        )

    def _point_value(
        self,
        *,
        datasets: list[xr.Dataset],
        variable: str,
        latitude: float,
        longitude: float,
    ) -> float:
        dataset = self._find_dataset(datasets, variable)

        if "latitude" not in dataset.coords:
            raise WeatherProviderError(
                "ECMWF dataset has no latitude coordinate"
            )

        lon = longitude_for_dataset(
            longitude,
            dataset_uses_360=self._dataset_uses_360(dataset),
        )

        # xarray interpolation is deterministic on a monotonic coordinate.
        ds = dataset.sortby("latitude").sortby("longitude")
        point = ds[variable].interp(
            latitude=float(latitude),
            longitude=float(lon),
            method="linear",
        )

        value = float(point.item())
        if value != value:  # NaN
            raise WeatherProviderError(
                "requested point is outside the ECMWF grid"
            )
        return value

    def _load_point_fields(
        self,
        *,
        wind_asset: CachedAsset,
        precip_asset: CachedAsset,
        previous_precip_asset: CachedAsset | None,
        latitude: float,
        longitude: float,
        interval_hours: float,
    ) -> tuple[float, float, float, float]:
        wind_sets = self._dataset_loader(wind_asset.path)
        precip_sets = self._dataset_loader(precip_asset.path)

        u10 = self._point_value(
            datasets=wind_sets,
            variable="u10",
            latitude=latitude,
            longitude=longitude,
        )
        v10 = self._point_value(
            datasets=wind_sets,
            variable="v10",
            latitude=latitude,
            longitude=longitude,
        )

        current_tp_m = self._point_value(
            datasets=precip_sets,
            variable="tp",
            latitude=latitude,
            longitude=longitude,
        )
        current_tp_mm = precipitation_m_to_mm(current_tp_m)

        if previous_precip_asset is None:
            previous_tp_mm = 0.0
        else:
            previous_sets = self._dataset_loader(
                previous_precip_asset.path
            )
            previous_tp_m = self._point_value(
                datasets=previous_sets,
                variable="tp",
                latitude=latitude,
                longitude=longitude,
            )
            previous_tp_mm = precipitation_m_to_mm(
                previous_tp_m
            )

        interval_mm, rate_mm_h = deaccumulate_precipitation_mm(
            previous_accumulation_mm=previous_tp_mm,
            current_accumulation_mm=current_tp_mm,
            interval_hours=interval_hours,
        )

        return u10, v10, current_tp_mm, rate_mm_h

    def get_point(
        self,
        *,
        latitude: float,
        longitude: float,
        valid_time: datetime | None = None,
    ) -> WeatherPoint:
        errors: list[str] = []

        for source_index, source in enumerate(self.sources):
            try:
                client = self._client(source)
                run = client.latest(
                    type="fc",
                    step=3,
                    param="10u",
                )
                run = _utc(run)

                step = self._select_step(
                    run=run,
                    requested_valid_time=valid_time,
                    now=self._now_fn(),
                )
                previous_step = self._previous_step(
                    run=run,
                    step=step,
                )

                wind_asset = self._retrieve_asset(
                    client=client,
                    source=source,
                    run=run,
                    step=step,
                    params=["10u", "10v"],
                    kind="wind",
                )
                precip_asset = self._retrieve_asset(
                    client=client,
                    source=source,
                    run=run,
                    step=step,
                    params=["tp"],
                    kind="tp",
                )

                previous_precip_asset = None
                if previous_step > 0:
                    previous_precip_asset = self._retrieve_asset(
                        client=client,
                        source=source,
                        run=run,
                        step=previous_step,
                        params=["tp"],
                        kind="tp",
                    )

                interval_hours = float(step - previous_step)
                (
                    u10,
                    v10,
                    cumulative_tp_mm,
                    rate_mm_h,
                ) = self._load_point_fields(
                    wind_asset=wind_asset,
                    precip_asset=precip_asset,
                    previous_precip_asset=previous_precip_asset,
                    latitude=latitude,
                    longitude=longitude,
                    interval_hours=interval_hours,
                )

                actual_valid_time = run + timedelta(hours=step)
                interval_start = run + timedelta(
                    hours=previous_step
                )

                data_sources = {
                    wind_asset.source,
                    precip_asset.source,
                }
                retrieved_times = [
                    wind_asset.retrieved_at,
                    precip_asset.retrieved_at,
                ]
                if previous_precip_asset is not None:
                    data_sources.add(
                        previous_precip_asset.source
                    )
                    retrieved_times.append(
                        previous_precip_asset.retrieved_at
                    )

                quality_flags = [
                    "spatial_interpolation_linear_native_grid",
                    "precipitation_deaccumulated_same_run",
                    "no_temporal_interpolation",
                ]

                requested = (
                    _utc(valid_time)
                    if valid_time is not None
                    else _utc(self._now_fn())
                )
                if abs(
                    (
                        actual_valid_time - requested
                    ).total_seconds()
                ) > 1.0:
                    quality_flags.append(
                        "valid_time_snapped_forward_to_model_step"
                    )

                fallback_used = (
                    source_index > 0
                    or any(
                        data_source != self.sources[0]
                        for data_source in data_sources
                    )
                )
                if fallback_used:
                    quality_flags.append("provider_mirror_fallback")

                return WeatherPoint(
                    latitude=float(latitude),
                    longitude=float(longitude),
                    wind_u_10m_ms=u10,
                    wind_v_10m_ms=v10,
                    wind_speed_10m_ms=wind_speed_ms(u10, v10),
                    wind_from_direction_deg=wind_from_direction_deg(
                        u10,
                        v10,
                    ),
                    precipitation_rate_mm_h=rate_mm_h,
                    precipitation_accumulation_mm=cumulative_tp_mm,
                    precipitation_interval_start=interval_start,
                    precipitation_interval_end=actual_valid_time,
                    provenance=WeatherProvenance(
                        provider="ecmwf",
                        model=self.model,
                        product=f"open-data-{self.resolution}",
                        data_kind="forecast",
                        forecast_reference_time=run,
                        valid_time=actual_valid_time,
                        retrieved_at=max(retrieved_times),
                        source_uri=",".join(sorted(data_sources)),
                        fallback_used=fallback_used,
                        quality_flags=quality_flags,
                    ),
                )
            except Exception as exc:
                errors.append(
                    f"{source}: {type(exc).__name__}: {exc}"
                )

        raise WeatherSourceUnavailable(
            "all ECMWF Open Data sources failed: "
            + " | ".join(errors)
        )
