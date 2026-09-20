from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.services.geos_cf_provider import (
    GeosCFProvider,
    product_info,
)


def _parse_utc(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _utc_iso(value: datetime) -> str:
    return (
        value.astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_freshness(
    field: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)

    run_time = _parse_utc(field["run_time"])
    valid_time = _parse_utc(field["valid_time"])

    run_age_hours = (now - run_time).total_seconds() / 3600.0
    valid_offset_hours = (valid_time - now).total_seconds() / 3600.0

    if valid_offset_hours > 0.75:
        relation = "future"
    elif valid_offset_hours < -0.75:
        relation = "past"
    else:
        relation = "near_now"

    return {
        "evaluated_at": _utc_iso(now),
        "run_age_hours": round(run_age_hours, 3),
        "valid_time_offset_hours_from_now": round(
            valid_offset_hours,
            3,
        ),
        "valid_time_relation": relation,
        "note": (
            "Freshness values are descriptive only. "
            "Fallback/cross-check thresholds are applied separately."
        ),
    }


def build_cams_comparison_metadata(
    product: str,
) -> dict[str, Any]:
    info = product_info(product)
    unit_compatible = bool(info["direct_cams_unit_comparison"])

    if unit_compatible:
        note = (
            "Native units are mass concentration compatible with CAMS µg/m³, "
            "but model products are not assumed scientifically equivalent. "
            "Cross-check requires valid-time alignment and explicit comparison "
            "logic."
        )
    else:
        note = (
            "Native GEOS-CF gas unit is mol/mol while the current CAMS field "
            "uses mass concentration. A physically explicit conversion step "
            "is required before numerical comparison."
        )

    return {
        "target_model": "CAMS Europe ensemble",
        "unit_compatible": unit_compatible,
        "direct_value_comparison_ready": False,
        "requires_valid_time_alignment": True,
        "requires_unit_conversion": not unit_compatible,
        "scientific_equivalence_assumed": False,
        "note": note,
    }


def normalize_geos_cf_field(
    field: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    longitude = field.get("longitude") or []
    latitude = field.get("latitude") or []
    values = field.get("values") or []

    if len(values) != len(latitude):
        raise ValueError(
            "GEOS-CF canonical field row count does not match latitude."
        )
    if any(len(row) != len(longitude) for row in values):
        raise ValueError(
            "GEOS-CF canonical field column count does not match longitude."
        )

    if any(
        longitude[i] >= longitude[i + 1]
        for i in range(len(longitude) - 1)
    ):
        raise ValueError("GEOS-CF longitude must be strictly ascending.")

    if any(
        latitude[i] >= latitude[i + 1]
        for i in range(len(latitude) - 1)
    ):
        raise ValueError("GEOS-CF latitude must be strictly ascending.")

    result = dict(field)
    result["freshness"] = build_freshness(field, now=now)
    result["cams_comparison"] = build_cams_comparison_metadata(
        field["product"]
    )
    return result


def fetch_geos_cf_field(
    *,
    product: str = "pm25",
    time_index: int = 0,
    stride: int = 1,
    provider: GeosCFProvider | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    provider = provider or GeosCFProvider()
    field = provider.fetch_field(
        product=product,
        time_index=time_index,
        stride=stride,
    )
    return normalize_geos_cf_field(
        field,
        now=now,
    )
