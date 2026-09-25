def build_evidence_timeline(
    pollutant="PM10",
):
    return {
        "pollutant": pollutant,
        "series": [
            {
                "source": "EEA",
                "source_type": "station_measurement",
                "points": [],
            },
            {
                "source": "CAMS",
                "source_type": "model_forecast",
                "points": [],
            },
            {
                "source": "Sentinel-5P",
                "source_type": "satellite_observation",
                "points": [],
            },
        ],
    }
