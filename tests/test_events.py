def test_create_event(client):

    response = client.post(
        "/events/",
        json={
            "id": "test_event_001",

            "category": "wildfire",

            "location": {
                "latitude": 44.56,
                "longitude": 38.07
            },

            "timestamp":
            "2026-09-11T18:00:00Z",

            "severity":
            "high",

            "confidence":
            0.85,

            "description":
            "Test wildfire event",

            "evidences": [
                {
                    "type": "news_report",

                    "description":
                    "Local reports about possible pollution",

                    "confidence": 0.65,

                    "source": {
                        "type": "news",

                        "name":
                        "Black Sea News",

                        "reliability":
                        0.6
                    }
                }
            ]
        }
    )


    assert response.status_code == 200


    data = response.json()


    assert data["status"] == "created"

    assert data["event"]["id"] == "test_event_001"