from __future__ import annotations

import argparse
import html
import json
import math
import sqlite3
import sys
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(
    "validation/gee_sentinel1_dark_spot_candidates_v01.json"
)
DEFAULT_DB = Path("database/events.db")
DEFAULT_HTML = Path(
    "validation/sat7c_dark_spot_verification_v01.html"
)
DEFAULT_SUMMARY = Path(
    "validation/sat7c_dark_spot_verification_v01.json"
)


class VerificationError(ValueError):
    """Raised when SAT-7C verification input is invalid."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "SAT-7C visual/spatial verification for Sentinel-1 "
            "SAR dark-spot candidates. Generates an OSM/Leaflet map "
            "and a compact verification summary. Does not write to "
            "EventStore and does not confirm pollution."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
    )
    parser.add_argument(
        "--events-db",
        type=Path,
        default=DEFAULT_DB,
    )
    parser.add_argument(
        "--html-output",
        type=Path,
        default=DEFAULT_HTML,
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=DEFAULT_SUMMARY,
    )

    return parser


def load_json_object(
    path: str | Path,
    *,
    label: str,
) -> dict[str, Any]:
    json_path = Path(path)

    try:
        data = json.loads(
            json_path.read_text(
                encoding="utf-8"
            )
        )
    except FileNotFoundError as exc:
        raise VerificationError(
            f"{label} file not found: {json_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise VerificationError(
            f"invalid {label} JSON: {json_path}"
        ) from exc

    if not isinstance(data, dict):
        raise VerificationError(
            f"{label} root must be a JSON object"
        )

    return data


def validate_candidate_payload(
    payload: dict[str, Any],
) -> None:
    if payload.get("information_type") != (
        "satellite_observation"
    ):
        raise VerificationError(
            "information_type must be 'satellite_observation'"
        )

    if payload.get("derivation_level") != "derived":
        raise VerificationError(
            "derivation_level must be 'derived'"
        )

    if payload.get("observation_type") != (
        "sar_dark_spot_candidate"
    ):
        raise VerificationError(
            "observation_type must be "
            "'sar_dark_spot_candidate'"
        )

    candidates = payload.get("candidates")

    if not isinstance(candidates, list):
        raise VerificationError(
            "candidates must be a list"
        )


def bbox_center(
    bbox: list[float],
) -> tuple[float, float]:
    if (
        not isinstance(bbox, list)
        or len(bbox) != 4
    ):
        raise VerificationError(
            "candidate bbox must have four values"
        )

    min_lon, min_lat, max_lon, max_lat = [
        float(value)
        for value in bbox
    ]

    return (
        (min_lat + max_lat) / 2.0,
        (min_lon + max_lon) / 2.0,
    )


def haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    radius_km = 6371.0088

    phi1 = math.radians(
        lat1
    )
    phi2 = math.radians(
        lat2
    )
    dphi = math.radians(
        lat2 - lat1
    )
    dlambda = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(
            dphi / 2.0
        ) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(
            dlambda / 2.0
        ) ** 2
    )

    c = 2.0 * math.atan2(
        math.sqrt(a),
        math.sqrt(1.0 - a),
    )

    return radius_km * c


def load_event_points(
    db_path: str | Path,
) -> list[dict[str, Any]]:
    path = Path(db_path)

    if not path.exists():
        return []

    uri = (
        path.resolve().as_uri()
        + "?mode=ro"
    )

    try:
        connection = sqlite3.connect(
            uri,
            uri=True,
        )
    except sqlite3.Error:
        return []

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                category,
                location_name,
                status,
                latitude,
                longitude
            FROM events
            WHERE latitude IS NOT NULL
              AND longitude IS NOT NULL
            ORDER BY updated_at DESC
            """
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        connection.close()

    return [
        {
            "id": row[0],
            "category": row[1],
            "location_name": row[2],
            "status": row[3],
            "latitude": float(row[4]),
            "longitude": float(row[5]),
        }
        for row in rows
    ]


def candidate_summaries(
    payload: dict[str, Any],
    event_points: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summaries = []

    for candidate in payload.get(
        "candidates",
        [],
    ):
        candidate_id = candidate.get(
            "candidate_id"
        )
        bbox = candidate.get(
            "bbox"
        )

        if not candidate_id or bbox is None:
            continue

        center_lat, center_lon = (
            bbox_center(
                bbox
            )
        )

        nearest_event = None

        for event in event_points:
            distance_km = haversine_km(
                center_lat,
                center_lon,
                event["latitude"],
                event["longitude"],
            )

            if (
                nearest_event is None
                or distance_km
                < nearest_event[
                    "distance_km"
                ]
            ):
                nearest_event = {
                    "event_id": event[
                        "id"
                    ],
                    "location_name": event[
                        "location_name"
                    ],
                    "category": event[
                        "category"
                    ],
                    "status": event[
                        "status"
                    ],
                    "distance_km": (
                        distance_km
                    ),
                }

        summaries.append(
            {
                "candidate_id": (
                    candidate_id
                ),
                "area_km2": candidate.get(
                    "area_km2"
                ),
                "mean_vv_db": candidate.get(
                    "mean_vv_db"
                ),
                "review_status": (
                    candidate.get(
                        "review_status"
                    )
                ),
                "confidence": candidate.get(
                    "confidence"
                ),
                "bbox": bbox,
                "bbox_center": {
                    "latitude": (
                        center_lat
                    ),
                    "longitude": (
                        center_lon
                    ),
                },
                "nearest_event": (
                    nearest_event
                ),
            }
        )

    return summaries


def pairwise_candidate_distances(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    distances = []

    for left_index in range(
        len(candidates)
    ):
        for right_index in range(
            left_index + 1,
            len(candidates),
        ):
            left = candidates[
                left_index
            ]
            right = candidates[
                right_index
            ]

            left_center = left[
                "bbox_center"
            ]
            right_center = right[
                "bbox_center"
            ]

            distances.append(
                {
                    "candidate_a": left[
                        "candidate_id"
                    ],
                    "candidate_b": right[
                        "candidate_id"
                    ],
                    "distance_km": (
                        haversine_km(
                            left_center[
                                "latitude"
                            ],
                            left_center[
                                "longitude"
                            ],
                            right_center[
                                "latitude"
                            ],
                            right_center[
                                "longitude"
                            ],
                        )
                    ),
                }
            )

    return distances


def build_summary(
    payload: dict[str, Any],
    event_points: list[dict[str, Any]],
) -> dict[str, Any]:
    candidates = candidate_summaries(
        payload,
        event_points,
    )

    return {
        "verification_version": "0.1",
        "information_type": (
            "satellite_observation"
        ),
        "derivation_level": (
            "derived"
        ),
        "verification_type": (
            "visual_spatial_review"
        ),
        "source_observation_type": (
            payload.get(
                "observation_type"
            )
        ),
        "source_scene": payload.get(
            "source_scene"
        ),
        "analysis": payload.get(
            "analysis"
        ),
        "summary": payload.get(
            "summary"
        ),
        "candidate_count": len(
            candidates
        ),
        "candidates": candidates,
        "pairwise_candidate_distances_km": (
            pairwise_candidate_distances(
                candidates
            )
        ),
        "event_overlay_count": len(
            event_points
        ),
        "semantics": {
            "review_mode": (
                "human_visual_context"
            ),
            "does_not_mean": [
                "oil_spill",
                "confirmed_pollution",
                "confirmed_event",
                "causal_link_to_event",
            ],
        },
    }


def _json_for_script(
    value: Any,
) -> str:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
        )
        .replace(
            "</",
            "<\\/",
        )
    )


def build_html(
    payload: dict[str, Any],
    summary: dict[str, Any],
) -> str:
    candidates_geojson = {
        "type": "FeatureCollection",
        "features": [],
    }

    candidate_lookup = {
        item["candidate_id"]: item
        for item in summary[
            "candidates"
        ]
    }

    for candidate in payload.get(
        "candidates",
        [],
    ):
        candidate_id = candidate.get(
            "candidate_id"
        )

        if not candidate_id:
            continue

        candidates_geojson[
            "features"
        ].append(
            {
                "type": "Feature",
                "properties": {
                    "candidate_id": (
                        candidate_id
                    ),
                    "area_km2": (
                        candidate.get(
                            "area_km2"
                        )
                    ),
                    "mean_vv_db": (
                        candidate.get(
                            "mean_vv_db"
                        )
                    ),
                    "nearest_event": (
                        candidate_lookup.get(
                            candidate_id,
                            {},
                        ).get(
                            "nearest_event"
                        )
                    ),
                },
                "geometry": candidate.get(
                    "geometry"
                ),
            }
        )

    aoi_bbox = (
        payload.get(
            "aoi",
            {},
        ).get(
            "bbox"
        )
    )

    source_scene = payload.get(
        "source_scene",
        {},
    )

    semantics = payload.get(
        "semantics",
        {},
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SAT-7C Dark-Spot Verification</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
html, body, #map {{
    height: 100%;
    margin: 0;
}}
#panel {{
    position: absolute;
    z-index: 1000;
    top: 12px;
    left: 52px;
    max-width: 420px;
    background: rgba(255,255,255,0.95);
    padding: 12px 14px;
    border-radius: 8px;
    font: 14px/1.4 system-ui, sans-serif;
    box-shadow: 0 1px 8px rgba(0,0,0,0.25);
}}
#panel strong {{
    display: block;
    margin-bottom: 4px;
}}
.small {{
    font-size: 12px;
    color: #444;
}}
</style>
</head>
<body>
<div id="panel">
<strong>SAT-7C · visual/spatial verification</strong>
<div>Scene: {html.escape(str(source_scene.get("scene_id", "")))}</div>
<div>Candidate polygons: {len(candidates_geojson["features"])}</div>
<div class="small">
Dark-spot candidates only. Not oil, not confirmed pollution,
not event confirmation.
</div>
</div>
<div id="map"></div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const candidates = {_json_for_script(candidates_geojson)};
const aoiBbox = {_json_for_script(aoi_bbox)};
const events = {_json_for_script(summary.get("candidates", []))};
const map = L.map("map");

const esriSatellite = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}",
    {{
        maxZoom: 19,
        attribution: "Tiles &copy; Esri"
    }}
);

const esriStreets = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}",
    {{
        maxZoom: 19,
        attribution: "Tiles &copy; Esri"
    }}
);

esriSatellite.addTo(map);

L.control.layers(
    {{
        "Esri Satellite": esriSatellite,
        "Esri Streets": esriStreets
    }}
).addTo(map);

function candidatePopup(feature) {{
    const p = feature.properties || {{}};
    const nearest = p.nearest_event;
    let text =
        "<b>" + (p.candidate_id || "candidate") + "</b>" +
        "<br>area: " + Number(p.area_km2 || 0).toFixed(5) + " km²" +
        "<br>mean VV: " + Number(p.mean_vv_db || 0).toFixed(2) + " dB";
    if (nearest) {{
        text +=
            "<br>nearest stored event: " + nearest.location_name +
            "<br>distance: " + Number(nearest.distance_km).toFixed(2) + " km";
    }}
    text +=
        "<br><i>Candidate only — not a pollution confirmation.</i>";
    return text;
}}

const candidateLayer = L.geoJSON(
    candidates,
    {{
        style: {{
            weight: 2,
            fillOpacity: 0.25
        }},
        onEachFeature: function(feature, layer) {{
            layer.bindPopup(candidatePopup(feature));
        }}
    }}
).addTo(map);

if (aoiBbox && aoiBbox.length === 4) {{
    const bounds = [
        [aoiBbox[1], aoiBbox[0]],
        [aoiBbox[3], aoiBbox[2]]
    ];
    L.rectangle(
        bounds,
        {{
            weight: 1,
            dashArray: "6 4",
            fill: false
        }}
    ).addTo(map);
}}

const pointGroup = L.featureGroup().addTo(map);

if (aoiBbox && aoiBbox.length === 4) {{
    const aoiCenter = [
        (aoiBbox[1] + aoiBbox[3]) / 2,
        (aoiBbox[0] + aoiBbox[2]) / 2
    ];

    L.marker(aoiCenter)
        .addTo(map)
        .bindPopup(
            "<b>Novorossiysk AOI</b><br>" +
            "Sentinel-1 SAR dark-spot candidate review area"
        );
}}

events.forEach(function(item) {{
    const center = item.bbox_center;
    if (!center) return;

    let popup =
        "<b>" + item.candidate_id + " bbox center</b>" +
        "<br>lat: " + center.latitude.toFixed(6) +
        "<br>lon: " + center.longitude.toFixed(6);

    if (item.nearest_event) {{
        popup +=
            "<br>nearest stored event: " +
            item.nearest_event.location_name +
            "<br>distance: " +
            item.nearest_event.distance_km.toFixed(2) +
            " km";
    }}

    L.circleMarker(
        [center.latitude, center.longitude],
        {{
            radius: 5,
            weight: 1,
            fillOpacity: 0.8
        }}
    ).bindPopup(popup).addTo(pointGroup);
}});

if (aoiBbox && aoiBbox.length === 4) {{
    const aoiBounds = [
        [aoiBbox[1], aoiBbox[0]],
        [aoiBbox[3], aoiBbox[2]]
    ];

    map.fitBounds(
        aoiBounds,
        {{
            padding: [40, 40],
            maxZoom: 10
        }}
    );
}} else if (candidateLayer.getLayers().length > 0) {{
    map.fitBounds(
        candidateLayer.getBounds(),
        {{
            padding: [120, 120],
            maxZoom: 12
        }}
    );
}} else {{
    map.setView([44.72, 37.77], 11);
}}
</script>
</body>
</html>
"""


def main() -> int:
    args = build_parser().parse_args()

    try:
        payload = load_json_object(
            args.input,
            label="candidate",
        )
        validate_candidate_payload(
            payload
        )
    except VerificationError as exc:
        print(
            f"ERROR: {exc}"
        )
        return 2

    event_points = load_event_points(
        args.events_db
    )

    summary = build_summary(
        payload,
        event_points,
    )

    html_document = build_html(
        payload,
        summary,
    )

    args.summary_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    args.html_output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.summary_output.write_text(
        json.dumps(
            summary,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    args.html_output.write_text(
        html_document,
        encoding="utf-8",
    )

    print(
        "SAT-7C visual/spatial verification generated."
    )
    print(
        f"Candidates: {summary['candidate_count']}"
    )
    print(
        "Stored event overlay points available: "
        f"{summary['event_overlay_count']}"
    )

    for candidate in summary[
        "candidates"
    ]:
        center = candidate[
            "bbox_center"
        ]
        print(
            f"{candidate['candidate_id']}: "
            f"center=({center['latitude']:.6f}, "
            f"{center['longitude']:.6f}), "
            f"area={candidate['area_km2']:.5f} km2, "
            f"mean_vv={candidate['mean_vv_db']:.2f} dB"
        )

        nearest = candidate.get(
            "nearest_event"
        )

        if nearest:
            print(
                "  nearest stored event: "
                f"{nearest['location_name']} "
                f"({nearest['distance_km']:.2f} km)"
            )

    print(
        "Pairwise candidate center distances:"
    )

    for item in summary[
        "pairwise_candidate_distances_km"
    ]:
        print(
		f"  {item['candidate_a']} <-> "
		f"{item['candidate_b']}: "
            f"{item['distance_km']:.2f} km"
        )

    print(
        f"Summary: {args.summary_output}"
    )
    print(
        f"Map: {args.html_output}"
    )
    print(
        "Open the HTML file in a browser with internet access "
        "to load the OpenStreetMap basemap."
    )
    print(
        "SAT-7C verification does not confirm oil or pollution."
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )
