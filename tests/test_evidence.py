def test_get_event_evidence(client):

    response = client.post(
        "/events/",
        json={

            "id": "event_evidence_001",

            "category": "oil_spill",

            "location": {
                "latitude": 44.62,
                "longitude": 37.83
            },

            "timestamp":
            "2026-09-11T20:00:00Z",

            "severity":
            "high",

            "confidence":
            0.8,


            "description":
            "Possible oil pollution",


            "evidences": [

                {
                    "type":
                    "satellite_observation",

                    "description":
                    "Water surface anomaly detected",

                    "confidence":
                    0.85,


                    "source": {

                        "type":
                        "satellite",

                        "name":
                        "Sentinel-2",

                        "reliability":
                        0.9
                    }
                }
            ]
        }
    )


    assert response.status_code == 200



    evidence_response = client.get(
        "/events/event_evidence_001/evidence"
    )


    assert evidence_response.status_code == 200


    evidences = evidence_response.json()


    assert len(evidences) == 1

    assert (
        evidences[0]["type"]
        ==
        "satellite_observation"
    )