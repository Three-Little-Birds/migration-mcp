"""FastAPI application factory for migration MCP."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .core import generate_routes, list_datasets, list_tiles, refresh_datasets
from .models import AdminRefreshResponse, RouteRequest, RouteResponse


def create_app() -> FastAPI:
    app = FastAPI(
        title="Migration MCP Server",
        version="0.1.0",
        description="Generate surrogate or dataset-backed migration trajectories for agents.",
    )

    @app.post("/routes", response_model=RouteResponse)
    def post_routes(request: RouteRequest) -> RouteResponse:
        try:
            return generate_routes(request)
        except RuntimeError as exc:  # pragma: no cover
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/datasets")
    def get_datasets() -> dict[str, object]:
        return list_datasets()

    @app.get("/tiles")
    def get_tiles() -> dict[str, object]:
        return list_tiles()

    @app.post("/admin/refresh", response_model=AdminRefreshResponse)
    def post_refresh(request: RouteRequest | None = None, x_mcp_admin_token: str | None = None) -> AdminRefreshResponse:
        try:
            return refresh_datasets(request, x_mcp_admin_token)
        except RuntimeError as exc:  # pragma: no cover
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    return app


__all__ = ["create_app"]
