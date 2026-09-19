from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.impact_registry import router


app = FastAPI()
app.include_router(router)

client = TestClient(app)


def test_impact_registry_endpoint():
    response = client.get("/impact/registry")

    assert response.status_code == 200

    data = response.json()

    assert data["registry"] == "impact_registry_v01"
    assert data["count"] == 25
    assert len(data["targets"]) == 25

    names = {
        item["name"]
        for item in data["targets"]
    }

    assert "Novorossiysk Port" in names
    assert "Utrish Reserve" in names
