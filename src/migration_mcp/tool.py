"""python-sdk tool registration for migration MCP."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .core import generate_routes, list_datasets, list_tiles
from .models import RouteRequest, RouteResponse


def build_tool(app: FastMCP) -> None:
    """Register migration data access tools on an MCP server."""

    @app.tool(
        name="migration.generate_routes",
        description=(
            "Create migration paths from staged telemetry/BirdFlow data. "
            "Input species code, season, and optional filters. Returns GeoJSON routes and provenance."
        ),
        meta={"version": "0.1.0", "categories": ["migration", "planning"]},
    )
    def generate(request: RouteRequest) -> RouteResponse:
        return generate_routes(request)

    @app.tool(
        name="migration.list_datasets",
        description="List staged telemetry datasets detected under the configured data root.",
        meta={"version": "0.1.0", "categories": ["migration", "catalog"]},
    )
    def datasets() -> dict[str, object]:
        return list_datasets()

    @app.tool(
        name="migration.list_tiles",
        description="List cached BirdCast tiles and metadata that can support visualization layers.",
        meta={"version": "0.1.0", "categories": ["migration", "catalog"]},
    )
    def tiles() -> dict[str, object]:
        return list_tiles()


__all__ = ["build_tool"]
