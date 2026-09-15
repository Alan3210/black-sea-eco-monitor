import numpy as np
import pytest
import xarray as xr

from agents.ocean_data.openoil_validation import (
    OpenOilValidationInputError,
    build_constant_environment,
    select_model_seed_location,
    summarize_final_positions,
    summarize_mass_budget,
    validate_request,
)


def test_validate_request_accepts_small_engine_run():
    validate_request(
        hours=6,
        particles=100,
        radius_m=200,
        release_volume_m3=1,
    )


def test_validate_request_rejects_zero_volume():
    with pytest.raises(
        OpenOilValidationInputError
    ):
        validate_request(
            hours=6,
            particles=100,
            radius_m=200,
            release_volume_m3=0,
        )


def test_seed_location_prefers_sampled_ocean_cell():
    forcing = {
        "current": {
            "sampled_location": {
                "longitude": 37.825,
                "latitude": 44.7,
                "distance_km": 5.161,
                "method": "nearest_finite_ocean_cell",
            }
        }
    }

    result = select_model_seed_location(
        forcing,
        requested_longitude=37.7691,
        requested_latitude=44.724,
    )

    assert result["longitude"] == 37.825
    assert result["latitude"] == 44.7
    assert result["sampling_method"] == (
        "nearest_finite_ocean_cell"
    )


def test_build_constant_environment_maps_openoil_fields():
    forcing = {
        "openoil_ready_fields": {
            "x_sea_water_velocity": 0.01,
            "y_sea_water_velocity": -0.02,
            "x_wind": 4.2,
            "y_wind": 1.3,
            "sea_surface_wave_stokes_drift_x_velocity": 0.02,
            "sea_surface_wave_stokes_drift_y_velocity": 0.01,
            "sea_surface_wave_significant_height": 0.45,
        }
    }

    environment = build_constant_environment(
        forcing,
        temperature_c=20,
        salinity_psu=18,
    )

    assert environment[
        "x_wind"
    ] == 4.2
    assert environment[
        "sea_water_temperature"
    ] == 20
    assert environment[
        "sea_water_salinity"
    ] == 18


def test_summarize_final_positions():
    result = xr.Dataset(
        data_vars={
            "lon": (
                ("trajectory", "time"),
                np.array([
                    [37.0, 37.1],
                    [37.2, 37.3],
                ]),
            ),
            "lat": (
                ("trajectory", "time"),
                np.array([
                    [44.0, 44.1],
                    [44.2, 44.3],
                ]),
            ),
        },
        coords={
            "trajectory": [0, 1],
            "time": [0, 1],
        },
    )

    summary = summarize_final_positions(
        result
    )

    assert summary["particle_count"] == 2
    assert summary["center"] == {
        "longitude": 37.2,
        "latitude": 44.2,
    }


def test_summarize_mass_budget():
    result = xr.Dataset(
        data_vars={
            "mass_oil": (
                ("trajectory", "time"),
                np.array([
                    [10, 7],
                    [10, 8],
                ]),
            ),
            "mass_evaporated": (
                ("trajectory", "time"),
                np.array([
                    [0, 2],
                    [0, 1],
                ]),
            ),
            "mass_dispersed": (
                ("trajectory", "time"),
                np.array([
                    [0, 1],
                    [0, 1],
                ]),
            ),
            "mass_biodegraded": (
                ("trajectory", "time"),
                np.zeros(
                    (
                        2,
                        2,
                    )
                ),
            ),
            "water_fraction": (
                ("trajectory", "time"),
                np.array([
                    [0, 0.1],
                    [0, 0.3],
                ]),
            ),
            "fraction_evaporated": (
                ("trajectory", "time"),
                np.array([
                    [0, 0.2],
                    [0, 0.1],
                ]),
            ),
        },
        coords={
            "trajectory": [0, 1],
            "time": [0, 1],
        },
    )

    budget = summarize_mass_budget(
        result
    )

    assert budget[
        "remaining_oil_kg"
    ] == 15.0
    assert budget[
        "evaporated_kg"
    ] == 3.0
    assert budget[
        "dispersed_kg"
    ] == 2.0
    assert budget[
        "accounted_mass_kg"
    ] == 20.0
    assert budget[
        "mean_water_fraction"
    ] == pytest.approx(
        0.2
    )



def test_final_positions_use_each_trajectory_last_finite_observation():
    result = xr.Dataset(
        data_vars={
            "lon": (
                ("trajectory", "time"),
                np.array([
                    [37.0, 37.1, np.nan],
                    [38.0, 38.1, 38.2],
                ]),
            ),
            "lat": (
                ("trajectory", "time"),
                np.array([
                    [44.0, 44.1, np.nan],
                    [45.0, 45.1, 45.2],
                ]),
            ),
        },
        coords={
            "trajectory": [0, 1],
            "time": [0, 1, 2],
        },
    )

    summary = summarize_final_positions(
        result
    )

    assert summary["trajectory_count"] == 2
    assert summary["particle_count"] == 2
    assert summary["center"] == {
        "longitude": 37.65,
        "latitude": 44.65,
    }


def test_mass_budget_uses_last_finite_value_for_deactivated_trajectories():
    result = xr.Dataset(
        data_vars={
            "mass_oil": (
                ("trajectory", "time"),
                np.array([
                    [10.0, 9.0, np.nan],
                    [10.0, 8.0, 7.0],
                ]),
            ),
            "mass_evaporated": (
                ("trajectory", "time"),
                np.array([
                    [0.0, 1.0, np.nan],
                    [0.0, 1.0, 3.0],
                ]),
            ),
            "mass_dispersed": (
                ("trajectory", "time"),
                np.zeros((2, 3)),
            ),
            "mass_biodegraded": (
                ("trajectory", "time"),
                np.zeros((2, 3)),
            ),
            "water_fraction": (
                ("trajectory", "time"),
                np.array([
                    [0.0, 0.2, np.nan],
                    [0.0, 0.1, 0.3],
                ]),
            ),
            "fraction_evaporated": (
                ("trajectory", "time"),
                np.array([
                    [0.0, 0.1, np.nan],
                    [0.0, 0.1, 0.3],
                ]),
            ),
        },
        coords={
            "trajectory": [0, 1],
            "time": [0, 1, 2],
        },
    )

    budget = summarize_mass_budget(
        result
    )

    assert budget["initial_oil_kg"] == 20.0
    assert budget["remaining_oil_kg"] == 16.0
    assert budget["evaporated_kg"] == 4.0
    assert budget["accounted_mass_kg"] == 20.0
    assert budget["mass_closure_error_kg"] == 0.0
    assert budget["trajectories_with_mass"] == 2


def test_mass_budget_reports_closure_error():
    result = xr.Dataset(
        data_vars={
            "mass_oil": (
                ("trajectory", "time"),
                np.array([
                    [10.0, 8.0],
                ]),
            ),
            "mass_evaporated": (
                ("trajectory", "time"),
                np.array([
                    [0.0, 1.0],
                ]),
            ),
        },
        coords={
            "trajectory": [0],
            "time": [0, 1],
        },
    )

    budget = summarize_mass_budget(
        result
    )

    assert budget["initial_oil_kg"] == 10.0
    assert budget["accounted_mass_kg"] == 9.0
    assert budget["mass_closure_error_kg"] == -1.0
    assert budget["mass_closure_error_percent"] == -10.0
