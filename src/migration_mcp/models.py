"""Typed models for migration MCP."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

class RouteRequest(BaseModel):
    species_code: str | None = Field(default=None, description="Optional species code")
    data_root: str | None = Field(default=None, description="Override for dataset root")
    num_waypoints: int = Field(20, ge=3, le=500)
    cruise_velocity_m_s: float = Field(10.0, ge=0.0)
    trim_yaw_rad: float = Field(0.0)
    climb_rate_m_s: float = Field(0.0)
    timestep_s: float = Field(1.0, gt=0)
    label: str = Field("prototype", description="Label for generated trajectory")
    objective: str | None = Field(default=None, description="Optional mission objective")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RouteResponse(BaseModel):
    geojson: dict[str, Any]
    deckgl: list[dict[str, Any]]
    metadata: dict[str, Any]


class AdminRefreshResponse(BaseModel):
    refreshed: bool
    datasets: dict[str, int]
