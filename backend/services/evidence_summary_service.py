def build_evidence_summary():
    return {
        "sources": {
            "station_measurements": {
                "available": True,
            },
            "model_forecast": {
                "available": True,
            },
            "satellite_observation": {
                "available": True,
            },
        },
        "quality": {
            "fresh_records": 0,
            "stale_records": 0,
        },
    }
