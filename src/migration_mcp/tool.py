"""python-sdk tool registration for migration MCP."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .core import generate_routes, list_datasets, list_tiles
from .models import RouteRequest, RouteResponse


def build_tool(app: FastMCP) -> None:
    @app.tool()
    def generate(request: RouteRequest) -> RouteResponse:  # type: ignore[valid-type]
        return generate_routes(request)

    @app.tool()
    def datasets() -> dict[str, object]:
        return list_datasets()

    @app.tool()
    def tiles() -> dict[str, object]:
        return list_tiles()


__all__ = ["build_tool"]
