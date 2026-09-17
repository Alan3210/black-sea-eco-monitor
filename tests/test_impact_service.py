from backend.schemas.impact import (
    ImpactPosition,
    ImpactTarget,
)
from backend.services.impact_service import (
    analyze_drift_impact,
    build_targets_from_event_records,
    haversine_distance_km,
)


def _target(
    *,
    name="Novorossiysk",
    latitude=44.724,
    longitude=37.7691,
):
    return ImpactTarget(
        id="loc_test",
        name=name,
        type="city",
        position=ImpactPosition(
            latitude=latitude,
            longitude=longitude,
        ),
        location_confidence=0.9,
        coordinate_source="canonical_database",
    )


def _forecast():
    return {
        "model": "OpenDrift OceanDrift",
        "scope": "passive_surface_tracer_current_only",
        "horizons": [
            {
                "hours": 6,
                "time": "2026-09-17T06:00:00+00:00",
                "points": [
                    [37.7700, 44.7240],
                    [37.7800, 44.7240],
                ],
            },
            {
                "hours": 12,
                "time": "2026-09-17T12:00:00+00:00",
                "points": [
                    [37.9000, 44.8000],
                ],
            },
        ],
    }


def test_haversine_same_point_is_zero():
    distance = haversine_distance_km(
        latitude_a=44.724,
        longitude_a=37.7691,
        latitude_b=44.724,
        longitude_b=37.7691,
    )

    assert distance == 0.0


def test_build_targets_deduplicates_named_locations():
    records = [
        {
            "location": {
                "name": "Novorossiysk",
                "latitude": 44.724,
                "longitude": 37.7691,
                "type": "city",
                "confidence": 0.8,
                "source": "canonical_database",
            }
        },
        {
            "location": {
                "name": "Novorossiysk",
                "latitude": 44.724,
                "longitude": 37.7691,
                "type": "city",
                "confidence": 0.9,
                "source": "canonical_database",
            }
        },
    ]

    targets = build_targets_from_event_records(
        records
    )

    assert len(targets) == 1
    assert targets[0].name == "Novorossiysk"
    assert targets[0].location_confidence == 0.9


def test_impact_marks_near_target_as_potentially_affected():
    result = analyze_drift_impact(
        forecast=_forecast(),
        targets=[_target()],
        proximity_threshold_km=1.0,
    )

    assessment = result.assessments[0]

    assert assessment.potentially_affected is True
    assert assessment.first_exposure_hours == 6
    assert assessment.affected_horizons == [6]
    assert assessment.minimum_distance_km < 0.1


def test_impact_keeps_far_target_unaffected():
    result = analyze_drift_impact(
        forecast=_forecast(),
        targets=[
            _target(
                name="Far place",
                latitude=45.5,
                longitude=39.5,
            )
        ],
        proximity_threshold_km=1.0,
    )

    assessment = result.assessments[0]

    assert assessment.potentially_affected is False
    assert assessment.first_exposure_hours is None
    assert assessment.affected_horizons == []
    assert assessment.minimum_distance_km is not None


def test_impact_handles_forecast_with_no_points():
    result = analyze_drift_impact(
        forecast={
            "model": "OpenDrift OceanDrift",
            "horizons": [
                {
                    "hours": 6,
                    "points": [],
                }
            ],
        },
        targets=[_target()],
        proximity_threshold_km=5.0,
    )

    assessment = result.assessments[0]

    assert assessment.potentially_affected is False
    assert assessment.minimum_distance_km is None
    assert assessment.closest_horizon_hours is None


def test_affected_targets_sort_before_unaffected():
    result = analyze_drift_impact(
        forecast=_forecast(),
        targets=[
            _target(
                name="Far place",
                latitude=45.5,
                longitude=39.5,
            ),
            _target(),
        ],
        proximity_threshold_km=1.0,
    )

    assert result.assessments[0].potentially_affected is True
    assert result.assessments[1].potentially_affected is False
