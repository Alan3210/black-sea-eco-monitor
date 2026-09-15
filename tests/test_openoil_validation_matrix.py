from agents.ocean_data.openoil_validation_matrix import (
    ValidationCase,
    add_reference_deltas,
    build_validation_cases,
    choose_reference_row,
    classify_health,
    haversine_km,
    scenario_map,
    summarize_payload,
)


def test_smoke_profile_has_three_cases():
    cases = build_validation_cases(
        profile="smoke"
    )

    assert len(cases) == 3
    assert {
        case.scenario.key
        for case in cases
    } == set(
        scenario_map()
    )


def test_standard_profile_has_twenty_four_cases():
    cases = build_validation_cases(
        profile="standard"
    )

    assert len(cases) == 24


def test_full_profile_has_thirty_six_cases():
    cases = build_validation_cases(
        profile="full"
    )

    assert len(cases) == 36


def test_haversine_zero_distance():
    assert haversine_km(
        37,
        44,
        37,
        44,
    ) == 0


def test_choose_reference_uses_highest_particles_then_widest_box():
    rows = [
        {
            "case_id": "a",
            "particles": 100,
            "half_width_deg": 2.0,
            "final_center_longitude": 37.0,
            "final_center_latitude": 44.0,
            "error": None,
        },
        {
            "case_id": "b",
            "particles": 500,
            "half_width_deg": 1.0,
            "final_center_longitude": 37.0,
            "final_center_latitude": 44.0,
            "error": None,
        },
        {
            "case_id": "c",
            "particles": 500,
            "half_width_deg": 2.0,
            "final_center_longitude": 37.0,
            "final_center_latitude": 44.0,
            "error": None,
        },
    ]

    assert choose_reference_row(
        rows
    )["case_id"] == "c"


def test_add_reference_deltas_sets_zero_on_reference():
    rows = [
        {
            "case_id": "a",
            "scenario": "s",
            "hours": 6,
            "particles": 100,
            "half_width_deg": 1.0,
            "final_center_longitude": 37.0,
            "final_center_latitude": 44.0,
            "evaporated_percent": 4.0,
            "stranded_percent": 10.0,
            "error": None,
        },
        {
            "case_id": "b",
            "scenario": "s",
            "hours": 6,
            "particles": 500,
            "half_width_deg": 2.0,
            "final_center_longitude": 37.1,
            "final_center_latitude": 44.1,
            "evaporated_percent": 5.0,
            "stranded_percent": 20.0,
            "error": None,
        },
    ]

    add_reference_deltas(
        rows
    )

    reference = rows[1]

    assert reference[
        "reference_case_id"
    ] == "b"
    assert reference[
        "center_delta_km_to_reference"
    ] == 0.0
    assert reference[
        "evaporation_delta_pp_to_reference"
    ] == 0.0
    assert reference[
        "stranded_delta_pp_to_reference"
    ] == 0.0


def test_classify_health_terminal_complete():
    row = {
        "error": None,
        "all_elements_accounted": True,
        "trajectories_with_mass": 100,
        "particles": 100,
        "mass_closure_error_percent": 0.0,
        "forecast_complete": True,
        "physical_terminal_state": True,
    }

    assert classify_health(
        row
    ) == "TERMINAL_COMPLETE"
