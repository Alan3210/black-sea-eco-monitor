from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sys
from typing import Any

import requests

from backend.services.ground_station_source_registry import (
    BLACK_SEA_COUNTRIES,
    GROUND_STATION_SOURCES,
)


EEA_API = "https://eeadmz1-downloads-api-appservice.azurewebsites.net"

POLLUTANTS = ["PM2.5", "PM10", "NO2", "O3", "SO2", "CO"]
EEA_EXPECTED_BLACK_SEA = {"BG", "RO"}
EEA_EXPECTED_ABSENT = {"TR", "GE", "UA", "RU"}


class GroundStationSourceProbeError(RuntimeError):
    pass


def _get_json(
    session: requests.Session,
    url: str,
    *,
    timeout: float,
) -> Any:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _post_json(
    session: requests.Session,
    url: str,
    payload: dict[str, Any],
    *,
    timeout: float,
) -> Any:
    response = session.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def probe_eea(
    *,
    session: requests.Session | None = None,
    timeout: float = 45.0,
    include_summary: bool = True,
) -> dict[str, Any]:
    session = session or requests.Session()

    countries_payload = _get_json(
        session,
        f"{EEA_API}/Country",
        timeout=timeout,
    )

    if not isinstance(countries_payload, list):
        raise GroundStationSourceProbeError(
            "EEA /Country response is not a list."
        )

    countries = {
        str(item.get("countryCode", "")).upper(): item.get("countryName")
        for item in countries_payload
        if isinstance(item, dict)
    }

    present = sorted(EEA_EXPECTED_BLACK_SEA.intersection(countries))
    absent = sorted(EEA_EXPECTED_ABSENT.difference(countries))
    unexpected_present = sorted(EEA_EXPECTED_ABSENT.intersection(countries))

    result: dict[str, Any] = {
        "source": "eea",
        "api_base": EEA_API,
        "country_endpoint_status": "ok",
        "country_count": len(countries),
        "black_sea": {
            "supported": present,
            "expected_primary": sorted(EEA_EXPECTED_BLACK_SEA),
            "not_in_current_country_endpoint": absent,
            "unexpected_present": unexpected_present,
        },
        "dataset": {
            "id": 1,
            "name": "E2a / Up-To-Date",
            "semantics": "station_measurement_unverified",
            "aggregation": "hour",
        },
        "pollutants_requested": POLLUTANTS,
        "summary": {},
    }

    if include_summary:
        for country in sorted(EEA_EXPECTED_BLACK_SEA):
            payload = {
                "countries": [country],
                "cities": [],
                "pollutants": POLLUTANTS,
                "dataset": 1,
                "aggregationType": "hour",
                "source": "EkoKontur AIR-1.6A source validation",
            }
            summary = _post_json(
                session,
                f"{EEA_API}/DownloadSummary",
                payload,
                timeout=timeout,
            )
            result["summary"][country] = summary

    result["usable_for_primary_black_sea_station_layer"] = (
        set(present) == EEA_EXPECTED_BLACK_SEA
        and not unexpected_present
    )

    return result


def probe_official_portal(
    session: requests.Session,
    *,
    source_id: str,
    timeout: float,
) -> dict[str, Any]:
    source = GROUND_STATION_SOURCES[source_id]
    portal = source.get("portal")
    if not portal:
        return {
            "source": source_id,
            "status": "no_portal_url",
        }

    try:
        response = session.get(
            portal,
            timeout=timeout,
            allow_redirects=True,
        )
        return {
            "source": source_id,
            "portal": portal,
            "status_code": response.status_code,
            "reachable": response.ok,
            "final_url": response.url,
            "machine_api_validated": bool(source.get("machine_api") is True),
        }
    except requests.RequestException as exc:
        return {
            "source": source_id,
            "portal": portal,
            "reachable": False,
            "error": str(exc),
            "machine_api_validated": bool(source.get("machine_api") is True),
        }


def run_probe(
    *,
    timeout: float = 45.0,
    include_summary: bool = True,
) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "EkoKontur/0.1 AIR-1.6A ground-station source validation"
            )
        }
    )

    eea = probe_eea(
        session=session,
        timeout=timeout,
        include_summary=include_summary,
    )

    portals = [
        probe_official_portal(
            session,
            source_id=source_id,
            timeout=timeout,
        )
        for source_id in (
            "turkiye_havaizleme",
            "georgia_airgov",
            "ukraine_open_data",
        )
    ]

    return {
        "status": "ok",
        "checked_at": (
            datetime.now(timezone.utc)
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "black_sea_countries": BLACK_SEA_COUNTRIES,
        "decision": {
            "primary_machine_source": "eea",
            "primary_machine_scope": ["BG", "RO"],
            "local_provider_tracks_required": ["TR", "GE", "UA", "RU"],
            "openaq": "excluded",
            "note": (
                "EEA is suitable as the first production station provider, "
                "but it does not cover all Black Sea coastal states in its "
                "current /Country endpoint."
            ),
        },
        "eea": eea,
        "official_portals": portals,
        "source_registry": GROUND_STATION_SOURCES,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AIR-1.6A official ground-station source validation."
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=45.0,
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip EEA DownloadSummary calls.",
    )
    parser.add_argument(
        "--output",
        default="validation/air1_6a_ground_station_sources.json",
    )
    args = parser.parse_args()

    try:
        report = run_probe(
            timeout=args.timeout,
            include_summary=not args.no_summary,
        )
    except (
        requests.RequestException,
        GroundStationSourceProbeError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}")
        return 2

    from pathlib import Path

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )

    summary = {
        "status": report["status"],
        "checked_at": report["checked_at"],
        "decision": report["decision"],
        "eea_black_sea": report["eea"]["black_sea"],
        "eea_summary": report["eea"]["summary"],
        "official_portals": report["official_portals"],
        "report": str(output),
    }

    print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
