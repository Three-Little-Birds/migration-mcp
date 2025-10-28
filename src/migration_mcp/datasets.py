"""Dataset discovery helpers for migration MCP."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_DATA_ROOT = Path("~/bird-data").expanduser()
ROUTES_SUBDIR = Path("migration") / "routes"
BIRDFLOW_SUBDIR = ROUTES_SUBDIR / "birdflow"
BIRDCAST_TILES_SUBDIR = Path("migration") / "tiles" / "birdcast"
BIRDCAST_EXTENSIONS = {".tif", ".tiff", ".png", ".geojson"}
DATA_ROOT_ENV = "BIRD_MIGRATION_DATA_ROOT"


@dataclass(frozen=True)
class RouteDataset:
    species_code: str
    path: Path
    metadata: dict[str, Any]
    source: str


@dataclass(frozen=True)
class BirdCastTile:
    date: str
    product: str
    level: str | None
    x: int | None
    y: int | None
    path: Path


def resolve_data_root(override: str | None) -> Path:
    if override:
        return Path(override).expanduser()
    env_override = os.getenv(DATA_ROOT_ENV)
    if env_override:
        return Path(env_override).expanduser()
    return DEFAULT_DATA_ROOT


def routes_dir(root: Path) -> Path:
    return root / ROUTES_SUBDIR


def birdflow_dir(root: Path) -> Path:
    return root / BIRDFLOW_SUBDIR


def birdcast_tiles_dir(root: Path) -> Path:
    return root / BIRDCAST_TILES_SUBDIR


@lru_cache(maxsize=16)
def discover_route_datasets(root: str) -> dict[str, list[RouteDataset]]:
    base = Path(root)
    mapping: dict[str, list[RouteDataset]] = {}
    if not (base / ROUTES_SUBDIR).exists():
        return mapping

    for path in sorted((base / ROUTES_SUBDIR).rglob("*.geojson")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        metadata = payload.get("metadata") or {}
        species_code = _extract_species_code(path, payload)
        dataset = RouteDataset(
            species_code=species_code,
            path=path,
            metadata=metadata if isinstance(metadata, dict) else {},
            source="birdflow" if "birdflow" in path.parts else "geojson",
        )
        mapping.setdefault(species_code, []).append(dataset)

    for species, datasets in mapping.items():
        mapping[species] = sorted(
            datasets,
            key=lambda item: (0 if item.source == "birdflow" else 1, item.path.name.lower()),
        )

    return mapping


def list_route_datasets(root: Path) -> list[RouteDataset]:
    datasets: list[RouteDataset] = []
    for items in discover_route_datasets(str(root)).values():
        datasets.extend(items)
    return datasets


@lru_cache(maxsize=16)
def discover_birdcast_tiles(root: str) -> list[BirdCastTile]:
    tiles_root = Path(root) / BIRDCAST_TILES_SUBDIR
    tiles: list[BirdCastTile] = []
    if not tiles_root.exists():
        return tiles

    for path in sorted(tiles_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in BIRDCAST_EXTENSIONS:
            continue
        try:
            relative = path.relative_to(tiles_root)
        except ValueError:
            continue
        parts = relative.parts
        if len(parts) < 2:
            continue
        date, product = parts[0], parts[1]
        level = parts[2] if len(parts) >= 4 else None
        x_val = _coerce_int(parts[3]) if len(parts) >= 5 else None
        y_val = _coerce_int(Path(parts[4]).stem) if len(parts) >= 5 else None
        tiles.append(
            BirdCastTile(
                date=date,
                product=product,
                level=level,
                x=x_val,
                y=y_val,
                path=path,
            )
        )

    return tiles


def clear_caches() -> None:
    discover_route_datasets.cache_clear()
    discover_birdcast_tiles.cache_clear()


def _extract_species_code(path: Path, payload: dict[str, Any]) -> str:
    metadata = payload.get("metadata") or {}
    species_code = metadata.get("species_code") if isinstance(metadata, dict) else None
    if not species_code and isinstance(metadata.get("study_id"), str):
        species_code = path.stem.lower()
    if not species_code:
        features = payload.get("features")
        if isinstance(features, list) and features:
            props = (
                (features[0] or {}).get("properties", {}) if isinstance(features[0], dict) else {}
            )
            species_code = props.get("species_code") or props.get("taxon")
    if not species_code:
        species_code = path.stem
    return str(species_code).lower()


def _coerce_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
