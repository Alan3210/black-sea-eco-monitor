from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping
import json
import os
import time

import requests


TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
    "protocol/openid-connect/token"
)
PROCESS_URL = "https://sh.dataspace.copernicus.eu/process/v1"

# Process API expects [west, south, east, north].
DEFAULT_BLACK_SEA_BBOX = (26.0, 39.0, 43.5, 48.0)
DEFAULT_WIDTH = 350
DEFAULT_HEIGHT = 180

PRODUCTS: dict[str, dict[str, Any]] = {
    "no2": {
        "band": "NO2",
        "units": "mol/m^2",
        "quantity": "nitrogen_dioxide_tropospheric_column",
        "default_min_qa": 75,
    },
    "so2": {
        "band": "SO2",
        "units": "mol/m^2",
        "quantity": "sulfur_dioxide_total_column",
        "default_min_qa": 50,
    },
    "co": {
        "band": "CO",
        "units": "mol/m^2",
        "quantity": "carbon_monoxide_total_column",
        "default_min_qa": 50,
    },
    "o3": {
        "band": "O3",
        "units": "mol/m^2",
        "quantity": "ozone_total_column",
        "default_min_qa": 50,
    },
    "ch4": {
        "band": "CH4",
        "units": "ppb",
        "quantity": "methane_column_averaged_dry_air_mixing_ratio",
        "default_min_qa": 50,
    },
    "hcho": {
        "band": "HCHO",
        "units": "mol/m^2",
        "quantity": "formaldehyde_tropospheric_vertical_column",
        "default_min_qa": 50,
    },
    "aer_ai_340_380": {
        "band": "AER_AI_340_380",
        "units": "1",
        "quantity": "uv_aerosol_index_340_380",
        "default_min_qa": 50,
    },
    "aer_ai_354_388": {
        "band": "AER_AI_354_388",
        "units": "1",
        "quantity": "uv_aerosol_index_354_388",
        "default_min_qa": 50,
    },
}


class Sentinel5PError(RuntimeError):
    pass


@dataclass(frozen=True)
class Sentinel5PArtifact:
    path: Path
    metadata_path: Path
    cache_hit: bool
    metadata: Mapping[str, Any]


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = value.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def product_info(product: str) -> dict[str, Any]:
    key = product.strip().lower()
    try:
        return dict(PRODUCTS[key])
    except KeyError as exc:
        supported = ", ".join(sorted(PRODUCTS))
        raise ValueError(
            f"Unsupported Sentinel-5P product '{product}'. Supported: {supported}"
        ) from exc


def satellite_semantics(product: str) -> dict[str, Any]:
    info = product_info(product)
    return {
        "kind": "satellite_observation",
        "platform": "Sentinel-5P",
        "instrument": "TROPOMI",
        "level": "L2",
        "observation": True,
        "model_forecast": False,
        "station_measurement": False,
        "surface_concentration": False,
        "quantity": info["quantity"],
        "units": info["units"],
        "warning": (
            "Sentinel-5P/TROPOMI L2 is a satellite column/aerosol retrieval. "
            "It is not a ground-station measurement and must not be interpreted "
            "as surface PM2.5 or surface pollutant concentration."
        ),
    }


def build_evalscript(product: str) -> str:
    band = product_info(product)["band"]
    return f"""//VERSION=3
function setup() {{
  return {{
    input: ["{band}", "dataMask"],
    output: {{ bands: 2, sampleType: "FLOAT32" }}
  }};
}}

function evaluatePixel(sample) {{
  return [sample.{band}, sample.dataMask];
}}
"""


def build_process_request(
    *,
    product: str,
    start: datetime | str,
    end: datetime | str,
    bbox: tuple[float, float, float, float] = DEFAULT_BLACK_SEA_BBOX,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    min_qa: int | None = None,
    timeliness: str | None = None,
) -> dict[str, Any]:
    info = product_info(product)
    start_dt = _parse_datetime(start)
    end_dt = _parse_datetime(end)

    if end_dt <= start_dt:
        raise ValueError("Sentinel-5P end time must be later than start time.")
    if end_dt - start_dt > timedelta(hours=24):
        raise ValueError(
            "Sentinel-5P SIMPLE mosaicking window must not exceed 24 hours."
        )

    if len(bbox) != 4:
        raise ValueError("bbox must be [west, south, east, north].")
    west, south, east, north = map(float, bbox)
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("Invalid WGS84 bbox.")

    if not (1 <= int(width) <= 2500 and 1 <= int(height) <= 2500):
        raise ValueError("width and height must be between 1 and 2500 pixels.")

    qa = info["default_min_qa"] if min_qa is None else int(min_qa)
    if not 0 <= qa <= 100:
        raise ValueError("min_qa must be between 0 and 100.")

    data_filter: dict[str, Any] = {
        "timeRange": {
            "from": _utc_iso(start_dt),
            "to": _utc_iso(end_dt),
        },
        "mosaickingOrder": "mostRecent",
    }

    if timeliness:
        value = timeliness.strip().upper()
        if value not in {"NRTI", "OFFL", "RPRO"}:
            raise ValueError("timeliness must be one of NRTI, OFFL, RPRO.")
        data_filter["timeliness"] = value

    return {
        "input": {
            "bounds": {
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
                },
                "bbox": [west, south, east, north],
            },
            "data": [
                {
                    "type": "sentinel-5p-l2",
                    "dataFilter": data_filter,
                    "processing": {
                        "minQa": qa,
                        "upsampling": "NEAREST",
                    },
                }
            ],
        },
        "output": {
            "width": int(width),
            "height": int(height),
            "responses": [
                {
                    "identifier": "default",
                    "format": {"type": "image/tiff"},
                }
            ],
        },
        "evalscript": build_evalscript(product),
    }


class Sentinel5PProvider:
    def __init__(
        self,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        cache_dir: str | Path = "data/cache/air/sentinel5p",
        session: requests.Session | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.client_id = client_id or os.getenv("CDSE_SH_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("CDSE_SH_CLIENT_SECRET")
        self.cache_dir = Path(cache_dir)
        self.session = session or requests.Session()
        self.timeout = float(timeout)
        self._access_token: str | None = None
        self._token_expires_at = 0.0

    def _credentials_ready(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def _get_token(self) -> str:
        now = time.time()
        if self._access_token and now < self._token_expires_at - 60:
            return self._access_token

        if not self._credentials_ready():
            raise Sentinel5PError(
                "Missing CDSE Sentinel Hub OAuth credentials. Set "
                "CDSE_SH_CLIENT_ID and CDSE_SH_CLIENT_SECRET."
            )

        response = self.session.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except Exception as exc:
            raise Sentinel5PError(
                f"CDSE OAuth token request failed: HTTP "
                f"{getattr(response, 'status_code', 'unknown')}"
            ) from exc

        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise Sentinel5PError("CDSE OAuth response has no access_token.")

        expires_in = int(payload.get("expires_in", 3600))
        self._access_token = str(token)
        self._token_expires_at = now + max(120, expires_in)
        return self._access_token

    @staticmethod
    def _request_fingerprint(request_payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(
            request_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return sha256(canonical).hexdigest()[:20]

    def fetch_geotiff(
        self,
        *,
        product: str,
        start: datetime | str,
        end: datetime | str,
        bbox: tuple[float, float, float, float] = DEFAULT_BLACK_SEA_BBOX,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        min_qa: int | None = None,
        timeliness: str | None = None,
        force: bool = False,
    ) -> Sentinel5PArtifact:
        request_payload = build_process_request(
            product=product,
            start=start,
            end=end,
            bbox=bbox,
            width=width,
            height=height,
            min_qa=min_qa,
            timeliness=timeliness,
        )
        info = product_info(product)
        product_key = product.strip().lower()

        fingerprint = self._request_fingerprint(request_payload)
        target_dir = self.cache_dir / product_key
        target_dir.mkdir(parents=True, exist_ok=True)
        tiff_path = target_dir / f"{fingerprint}.tif"
        metadata_path = target_dir / f"{fingerprint}.json"

        if tiff_path.exists() and metadata_path.exists() and not force:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            return Sentinel5PArtifact(
                path=tiff_path,
                metadata_path=metadata_path,
                cache_hit=True,
                metadata=metadata,
            )

        token = self._get_token()
        response = self.session.post(
            PROCESS_URL,
            json=request_payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "image/tiff",
            },
            timeout=self.timeout,
        )

        try:
            response.raise_for_status()
        except Exception as exc:
            body = getattr(response, "text", "")[:500]
            raise Sentinel5PError(
                f"Sentinel Hub Process API failed: HTTP "
                f"{getattr(response, 'status_code', 'unknown')}. {body}"
            ) from exc

        content = bytes(response.content)
        if not content:
            raise Sentinel5PError("Sentinel Hub returned an empty GeoTIFF.")

        tiff_path.write_bytes(content)
        digest = sha256(content).hexdigest()
        now = datetime.now(timezone.utc)

        data_filter = request_payload["input"]["data"][0]["dataFilter"]
        processing = request_payload["input"]["data"][0]["processing"]

        metadata = {
            "provider": "Copernicus Data Space Ecosystem / Sentinel Hub",
            "collection": "sentinel-5p-l2",
            "platform": "Sentinel-5P",
            "instrument": "TROPOMI",
            "product": product_key,
            "band": info["band"],
            "quantity": info["quantity"],
            "units": info["units"],
            "semantics": satellite_semantics(product_key),
            "bbox": list(map(float, bbox)),
            "bbox_order": ["west", "south", "east", "north"],
            "width": int(width),
            "height": int(height),
            "time_from": data_filter["timeRange"]["from"],
            "time_to": data_filter["timeRange"]["to"],
            "timeliness": data_filter.get("timeliness"),
            "min_qa": processing["minQa"],
            "upsampling": processing["upsampling"],
            "sample_type": "FLOAT32",
            "bands": [info["band"], "dataMask"],
            "sha256": digest,
            "bytes": len(content),
            "fetched_at": _utc_iso(now),
            "process_endpoint": PROCESS_URL,
        }

        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return Sentinel5PArtifact(
            path=tiff_path,
            metadata_path=metadata_path,
            cache_hit=False,
            metadata=metadata,
        )
