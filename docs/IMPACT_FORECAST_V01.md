# Impact Forecast v0.1

Impact Forecast v0.1 adds the first impact-screening layer to ЭкоКонтур Черноморья.

## Goal

Move from:

```text
Where will the modeled drift go?
```

to:

```text
Which known places may come close to the modeled particle cloud?
```

## Scientific scope

v0.1 is deliberately a **proximity screening tool**.

It does **not** claim:

- confirmed shoreline impact;
- ecological damage;
- oiling of a protected area;
- beach closure;
- physical contact with a coastline polygon.

A target is marked `potentially_affected=true` only when at least one
forecast particle is within the configured `proximity_threshold_km`
at one of the forecast horizons.

## Target source

v0.1 reuses unique geolocated places already present in canonical EventStore.

Examples may include:

- cities;
- protected areas;
- other canonical location types already known by the event system.

This is intentionally temporary. Future versions should use dedicated
coastline, beach, settlement and protected-area datasets/polygons.

## Endpoints

### Known targets

```text
GET /impact/targets
```

### Analyze an existing OceanDrift forecast

```text
POST /impact/drift
```

Example body:

```json
{
  "proximity_threshold_km": 5.0,
  "forecast": {
    "model": "OpenDrift OceanDrift",
    "scope": "passive_surface_tracer_current_only",
    "horizons": [
      {
        "hours": 6,
        "time": "2026-09-17T06:00:00+00:00",
        "points": [
          [37.80, 44.72]
        ]
      }
    ]
  }
}
```

## Why POST takes an existing forecast

The endpoint intentionally does not launch OpenDrift/OpenOil/Copernicus.

This keeps Impact Forecast:

- fast;
- testable;
- compatible with cached/precomputed conference scenarios;
- independent from long-running model execution.

The current OceanDrift payload already exposes forecast horizons and
particle point clouds, which are sufficient for this first screening layer.

## Main response semantics

```text
potentially_affected
first_exposure_hours
first_exposure_time
minimum_distance_km
closest_horizon_hours
affected_horizons
```

`first_exposure_hours` is a forecast-horizon screening time, not a
continuous physical ETA.

## Next steps

v0.2:
- dedicated target registry;
- coastline / beach / settlement / protected-area geometry;
- polygon intersection and distance-to-coast;
- cached model-run IDs instead of resending full forecast JSON.

Later:
- OpenOil footprints;
- impact severity;
- biodiversity/habitat lookup;
- uncertainty and forcing freshness.
