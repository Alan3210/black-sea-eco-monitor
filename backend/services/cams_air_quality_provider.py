from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Iterable
import zipfile

CAMS_DATASET = "cams-europe-air-quality-forecasts"
CAMS_PROVIDER = "Copernicus Atmosphere Monitoring Service"
CAMS_MODEL = "ensemble"
CAMS_LEVEL = "0"
CAMS_PRODUCT_TYPE = "forecast"
CAMS_RUN_TIME = "00:00"
CAMS_DATA_FORMAT = "netcdf_zip"
DEFAULT_BLACK_SEA_AREA = (48.0, 26.0, 39.0, 43.5)  # N,W,S,E
DEFAULT_CACHE_DIR = Path("data/cache/air/cams-europe")

POLLUTANTS = {
    "pm25": {"ads_variable": "particulate_matter_2.5um", "label": "PM2.5", "units": "µg/m³", "quality_status": "validated"},
    "pm10": {"ads_variable": "particulate_matter_10um", "label": "PM10", "units": "µg/m³", "quality_status": "validated"},
    "no2": {"ads_variable": "nitrogen_dioxide", "label": "NO₂", "units": "µg/m³", "quality_status": "validated"},
    "so2": {"ads_variable": "sulphur_dioxide", "label": "SO₂", "units": "µg/m³", "quality_status": "validated"},
    "o3": {"ads_variable": "ozone", "label": "O₃", "units": "µg/m³", "quality_status": "validated"},
    "dust": {"ads_variable": "dust", "label": "Dust", "units": "µg/m³", "quality_status": "experimental"},
}
DEFAULT_POLLUTANTS = tuple(POLLUTANTS)

class CamsAirQualityError(RuntimeError): pass
class CamsConfigurationError(CamsAirQualityError): pass
class CamsRequestError(CamsAirQualityError): pass
class CamsArtifactError(CamsAirQualityError): pass

@dataclass(frozen=True)
class CamsAirArtifact:
    provider: str
    dataset: str
    model: str
    product_type: str
    run_date: str
    run_time_utc: str
    lead_hours: tuple[int, ...]
    pollutants: tuple[str, ...]
    area_nwse: tuple[float, float, float, float]
    data_format: str
    zip_path: str
    extracted_files: tuple[str, ...]
    metadata_path: str
    cache_hit: bool
    fetched_at: str | None
    sha256: str | None

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        for key in ("lead_hours", "pollutants", "area_nwse", "extracted_files"):
            out[key] = list(out[key])
        return out

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def normalize_run_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime): return value.astimezone(timezone.utc).date()
    if isinstance(value, date): return value
    if isinstance(value, str):
        try: return date.fromisoformat(value)
        except ValueError as exc: raise CamsRequestError(f"Invalid CAMS run date: {value!r}") from exc
    raise CamsRequestError(f"Unsupported CAMS run date type: {type(value)!r}")

def normalize_pollutants(values: Iterable[str] | None) -> tuple[str, ...]:
    result = tuple(dict.fromkeys(values or DEFAULT_POLLUTANTS))
    if not result: raise CamsRequestError("At least one CAMS pollutant is required.")
    unknown = [x for x in result if x not in POLLUTANTS]
    if unknown: raise CamsRequestError("Unsupported CAMS pollutant(s): " + ", ".join(unknown))
    return result

def normalize_lead_hours(values: Iterable[int | str]) -> tuple[int, ...]:
    parsed = []
    for raw in values:
        try: value = int(raw)
        except (TypeError, ValueError) as exc: raise CamsRequestError(f"Invalid CAMS lead hour: {raw!r}") from exc
        if value < 0 or value > 96: raise CamsRequestError(f"CAMS Europe forecast lead hour must be within 0..96, got {value}.")
        parsed.append(value)
    result = tuple(sorted(dict.fromkeys(parsed)))
    if not result: raise CamsRequestError("At least one CAMS lead hour is required.")
    return result

def normalize_area(area: Iterable[float] | None) -> tuple[float, float, float, float]:
    raw = tuple(float(x) for x in (area or DEFAULT_BLACK_SEA_AREA))
    if len(raw) != 4: raise CamsRequestError("CAMS area must contain [north, west, south, east].")
    north, west, south, east = raw
    if north <= south or east <= west: raise CamsRequestError("Invalid CAMS area ordering.")
    if north > 72 or south < 30 or west < -25 or east > 45:
        raise CamsRequestError("Requested area is outside the CAMS Europe domain.")
    return raw

def default_operational_run_date(now_utc: datetime | None = None) -> date:
    now = (now_utc or _utc_now()).astimezone(timezone.utc)
    cutoff = time(10, 15, tzinfo=timezone.utc)
    return now.date() if now.timetz() >= cutoff else now.date() - timedelta(days=1)

def build_cams_request(*, run_date, lead_hours, pollutants=None, area_nwse=None) -> dict[str, Any]:
    run = normalize_run_date(run_date)
    leads = normalize_lead_hours(lead_hours)
    species = normalize_pollutants(pollutants)
    area = normalize_area(area_nwse)
    iso = run.isoformat()
    return {
        "variable": [POLLUTANTS[x]["ads_variable"] for x in species],
        "model": [CAMS_MODEL],
        "level": [CAMS_LEVEL],
        "date": [f"{iso}/{iso}"],
        "type": [CAMS_PRODUCT_TYPE],
        "time": [CAMS_RUN_TIME],
        "leadtime_hour": [str(x) for x in leads],
        "data_format": CAMS_DATA_FORMAT,
        "area": list(area),
    }

def request_cache_key(request: dict[str, Any]) -> str:
    blob = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(blob).hexdigest()[:20]

def cams_configuration_status(home: Path | None = None) -> dict[str, Any]:
    path = (home or Path.home()) / ".cdsapirc"
    return {
        "configured": path.exists(),
        "config_path": str(path),
        "required_url": "https://ads.atmosphere.copernicus.eu/api",
        "minimum_cdsapi": "0.7.7",
        "licence_acceptance_required": True,
    }

def _sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()

def _safe_extract_zip(archive_path: Path, extract_dir: Path) -> tuple[Path, ...]:
    extract_dir.mkdir(parents=True, exist_ok=True)
    root = extract_dir.resolve()
    with zipfile.ZipFile(archive_path, "r") as z:
        members = z.infolist()
        if not members: raise CamsArtifactError("CAMS NetCDF ZIP is empty.")
        for member in members:
            dest = (extract_dir / member.filename).resolve()
            if dest != root and root not in dest.parents: raise CamsArtifactError("Unsafe path in CAMS ZIP artifact.")
        z.extractall(extract_dir)
    files = tuple(sorted(p for p in extract_dir.rglob("*") if p.is_file()))
    if not files: raise CamsArtifactError("CAMS ZIP did not contain any files.")
    return files

def _load_cdsapi_client():
    try: import cdsapi
    except ImportError as exc:
        raise CamsConfigurationError('Missing dependency "cdsapi>=0.7.7".') from exc
    try: return cdsapi.Client()
    except Exception as exc:
        raise CamsConfigurationError("Unable to initialise ADS cdsapi client. Check ~/.cdsapirc and dataset licence acceptance.") from exc

class CamsEuropeAirQualityProvider:
    def __init__(self, *, cache_dir=DEFAULT_CACHE_DIR, client_factory=None, now_factory=_utc_now):
        self.cache_dir = Path(cache_dir)
        self.client_factory = client_factory or _load_cdsapi_client
        self.now_factory = now_factory

    def retrieve(self, *, run_date, lead_hours, pollutants=None, area_nwse=None, force=False) -> CamsAirArtifact:
        run = normalize_run_date(run_date)
        leads = normalize_lead_hours(lead_hours)
        species = normalize_pollutants(pollutants)
        area = normalize_area(area_nwse)
        request = build_cams_request(run_date=run, lead_hours=leads, pollutants=species, area_nwse=area)
        key = request_cache_key(request)
        run_dir = self.cache_dir / run.isoformat() / key
        archive = run_dir / "cams-europe-air-quality.zip"
        extract_dir = run_dir / "netcdf"
        metadata_path = run_dir / "metadata.json"

        if not force and archive.exists() and metadata_path.exists() and extract_dir.exists():
            extracted = tuple(sorted(p for p in extract_dir.rglob("*") if p.is_file()))
            if extracted:
                meta = json.loads(metadata_path.read_text(encoding="utf-8"))
                return self._artifact(run, leads, species, area, archive, extracted, metadata_path, True, meta.get("fetched_at"), meta.get("artifact_sha256"))

        run_dir.mkdir(parents=True, exist_ok=True)
        if extract_dir.exists(): shutil_rmtree = __import__('shutil').rmtree; shutil_rmtree(extract_dir)
        client = self.client_factory()
        try: client.retrieve(CAMS_DATASET, request, str(archive))
        except Exception as exc: raise CamsAirQualityError("CAMS ADS retrieval failed.") from exc
        if not archive.exists(): raise CamsArtifactError("CAMS ADS client returned without creating the target ZIP.")
        if not zipfile.is_zipfile(archive): raise CamsArtifactError("CAMS ADS artifact is not a valid NetCDF ZIP.")
        extracted = _safe_extract_zip(archive, extract_dir)
        fetched_at = self.now_factory().astimezone(timezone.utc).isoformat()
        artifact_hash = _sha256_file(archive)
        metadata = {
            "provider": CAMS_PROVIDER, "dataset": CAMS_DATASET, "model": CAMS_MODEL,
            "product_type": CAMS_PRODUCT_TYPE, "run_date": run.isoformat(), "run_time_utc": CAMS_RUN_TIME,
            "lead_hours": list(leads), "pollutants": list(species),
            "pollutant_metadata": {x: POLLUTANTS[x] for x in species}, "area_nwse": list(area),
            "data_format": CAMS_DATA_FORMAT, "request": request, "fetched_at": fetched_at,
            "artifact_sha256": artifact_hash,
            "source_url": "https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts",
            "semantics": {"kind": "model_forecast", "observation": False, "station_measurement": False, "surface_concentration_units": "µg/m³ in NetCDF product"},
        }
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return self._artifact(run, leads, species, area, archive, extracted, metadata_path, False, fetched_at, artifact_hash)

    def _artifact(self, run, leads, species, area, archive, extracted, metadata_path, cache_hit, fetched_at, artifact_hash):
        return CamsAirArtifact(
            provider=CAMS_PROVIDER, dataset=CAMS_DATASET, model=CAMS_MODEL, product_type=CAMS_PRODUCT_TYPE,
            run_date=run.isoformat(), run_time_utc=CAMS_RUN_TIME, lead_hours=leads, pollutants=species,
            area_nwse=area, data_format=CAMS_DATA_FORMAT, zip_path=str(archive),
            extracted_files=tuple(str(x) for x in extracted), metadata_path=str(metadata_path),
            cache_hit=cache_hit, fetched_at=fetched_at, sha256=artifact_hash,
        )
