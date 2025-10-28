from __future__ import annotations

from fastapi.testclient import TestClient

from migration_mcp.fastapi_app import create_app


def test_routes_endpoint() -> None:
    client = TestClient(create_app())
    response = client.post("/routes", json={"num_waypoints": 6})
    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["status"] == "surrogate"
    assert len(payload["geojson"]["features"]) == 1
