from __future__ import annotations

from migration_mcp.core import generate_routes
from migration_mcp.models import RouteRequest


def test_generate_routes_surrogate() -> None:
    response = generate_routes(RouteRequest(num_waypoints=5, cruise_velocity_m_s=12.0))
    assert response.metadata["status"] == "surrogate"
    assert len(response.geojson["features"][0]["geometry"]["coordinates"]) == 5
    assert response.deckgl
