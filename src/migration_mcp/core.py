"""Scenario-agnostic migration route generation."""

from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path
from typing import Any

from .connectors import ensure_birdflow_route
from .datasets import (
    BirdCastTile,
    RouteDataset,
    clear_caches,
    discover_birdcast_tiles,
    discover_route_datasets,
    list_route_datasets,
    resolve_data_root,
)
from .models import AdminRefreshResponse, RouteRequest, RouteResponse

DATA_ROOT_ENV = "BIRD_MIGRATION_DATA_ROOT"
ADMIN_TOKEN_ENV = "MCP_MIGRATION_ADMIN_TOKEN"


def _data_root() -> Path:
    override = os.getenv(DATA_ROOT_ENV)
    return resolve_data_root(override)


def _resolve_request_root(value: str | None) -> Path:
    if value:
        return Path(value).expanduser()
    return resolve_data_root(None)


def _discover_datasets(data_root: Path | None = None) -> dict[str, list[RouteDataset]]:
    root = (data_root or _data_root()).expanduser()
    return discover_route_datasets(str(root))


def _list_datasets(data_root: Path | None = None) -> list[RouteDataset]:
    root = (data_root or _data_root()).expanduser()
    return list_route_datasets(root)


def _discover_birdcast(data_root: Path | None = None) -> list[BirdCastTile]:
    root = (data_root or _data_root()).expanduser()
    return discover_birdcast_tiles(str(root))


def _first_dataset(species_code: str, data_root: Path | None = None) -> RouteDataset | None:
    datasets = _discover_datasets(data_root)
    entries = datasets.get(species_code.lower())
    if entries:
        return entries[0]
    return None


def _load_geojson(dataset: RouteDataset) -> dict[str, Any]:
    try:
        return json.loads(dataset.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:  # pragma: no cover
        raise RuntimeError(f"Failed to read dataset {dataset.path}") from exc


def _resample_geojson(payload: dict[str, Any], target: int) -> dict[str, Any]:
    features = payload.get("features")
    if not isinstance(features, list) or not features:
        return payload
    feature = features[0]
    geometry = feature.get("geometry") or {}
    coords = geometry.get("coordinates")
    if not isinstance(coords, list):
        return payload
    if target <= 0 or len(coords) <= target:
        return payload
    indices = _select_indices(len(coords), target)
    resampled = [coords[idx] for idx in indices]
    geometry["coordinates"] = resampled
    feature["geometry"] = geometry
    properties = feature.get("properties") or {}
    timestamps = properties.get("timestamps")
    if isinstance(timestamps, list) and timestamps:
        properties["timestamps"] = [timestamps[idx] for idx in indices]
    feature["properties"] = properties
    payload["features"][0] = feature
    return payload


def _build_deckgl(payload: dict[str, Any]) -> list[dict[str, Any]]:
    features = payload.get("features")
    if not isinstance(features, list) or not features:
        return []
    feature = features[0]
    geometry = feature.get("geometry") or {}
    coords = geometry.get("coordinates")
    if not isinstance(coords, list) or not coords:
        return []
    properties = feature.get("properties") or {}
    timestamps = properties.get("timestamps")
    if not isinstance(timestamps, list):
        timestamps = list(range(len(coords)))
    altitudes = [coord[2] if len(coord) >= 3 else 0.0 for coord in coords]
    return [
        {
            "path": [coord[:2] for coord in coords],
            "timestamps": timestamps,
            "altitudes": altitudes,
            "label": properties.get("label") or properties.get("bird"),
        }
    ]


def _generate_surrogate_path(request: RouteRequest) -> tuple[list[list[float]], list[float]]:
    meters_to_deg = 1.0 / 111_320.0
    coords: list[list[float]] = []
    timestamps: list[float] = []
    cumulative_distance = 0.0

    for idx in range(request.num_waypoints):
        t = idx * request.timestep_s
        angle = request.trim_yaw_rad + 0.1 * math.sin(0.5 * t)
        step = max(request.cruise_velocity_m_s, 0.0) * request.timestep_s
        cumulative_distance += step
        x = cumulative_distance * math.cos(angle)
        y = cumulative_distance * math.sin(angle)
        lat = y * meters_to_deg
        lon = x * meters_to_deg
        alt = request.climb_rate_m_s * t
        coords.append([lon, lat, alt])
        timestamps.append(t)

    return coords, timestamps


def _select_indices(length: int, target: int) -> list[int]:
    if length <= 0:
        raise ValueError("Dataset must contain at least one coordinate")
    if target <= 0:
        return [0]
    if length <= target:
        return list(range(length))
    if target == 1:
        return [0]

    step = (length - 1) / (target - 1)
    indices = [round(i * step) for i in range(target)]
    deduped: list[int] = []
    prev = -1
    for idx in indices:
        if idx <= prev:
            idx = prev + 1
        if idx >= length:
            idx = length - 1
        deduped.append(idx)
        prev = idx
    return deduped


def generate_routes(request: RouteRequest) -> RouteResponse:
    data_root = _resolve_request_root(request.data_root)
    species_code = request.species_code.lower() if isinstance(request.species_code, str) else None
    metadata: dict[str, Any] = {
        "data_root": str(data_root),
        "requested_species": species_code,
        "waypoints": request.num_waypoints,
        "extra": request.metadata,
    }

    if species_code:
        dataset = _first_dataset(species_code, data_root)
        if not dataset:
            path = ensure_birdflow_route(species_code, data_root)
            if path:
                clear_caches()
                dataset = _first_dataset(species_code, data_root)
        if dataset:
            payload = _load_geojson(dataset)
            payload = _resample_geojson(payload, request.num_waypoints)
            deckgl = _build_deckgl(payload)
            metadata.update(
                {
                    "status": "dataset",
                    "dataset_path": str(dataset.path),
                    "dataset_source": dataset.source,
                }
            )
            return RouteResponse(geojson=payload, deckgl=deckgl, metadata=metadata)
        metadata["status"] = "fallback"

    coords, timestamps = _generate_surrogate_path(request)
    feature = {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": coords},
        "properties": {
            "label": request.label,
            "objective": request.objective,
            "timestamps": timestamps,
        },
    }
    geojson = {"type": "FeatureCollection", "features": [feature]}
    deckgl = _build_deckgl(copy.deepcopy(geojson))
    metadata.update({"status": "surrogate", "dataset_path": None, "dataset_source": None})
    return RouteResponse(geojson=geojson, deckgl=deckgl, metadata=metadata)


def list_datasets(data_root: Path | None = None) -> dict[str, Any]:
    root = data_root or _data_root()
    datasets = _list_datasets(root)
    return {"data_root": str(root), "datasets": [dataset.__dict__ for dataset in datasets]}


def list_tiles(data_root: Path | None = None) -> dict[str, Any]:
    root = data_root or _data_root()
    tiles = _discover_birdcast(root)
    return {"data_root": str(root), "tiles": [tile.__dict__ for tile in tiles]}


def refresh_datasets(request: RouteRequest | None, admin_token: str | None) -> AdminRefreshResponse:
    expected = os.getenv(ADMIN_TOKEN_ENV)
    if expected and expected != admin_token:
        raise RuntimeError("invalid admin token")

    payload = request or RouteRequest()
    refreshed = False
    if payload.species_code:
        refreshed = ensure_birdflow_route(payload.species_code) is not None
        if refreshed:
            clear_caches()
    clear_caches()
    datasets = _discover_datasets()
    stats = {species: len(entries) for species, entries in datasets.items()}
    return AdminRefreshResponse(refreshed=refreshed, datasets=stats)
