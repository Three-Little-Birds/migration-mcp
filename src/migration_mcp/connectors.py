"""Helpers for retrieving migration datasets via BirdFlow/BirdCast/Dryad connectors."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import requests

from .datasets import birdcast_tiles_dir, birdflow_dir, resolve_data_root, routes_dir

BIRDFLOW_FALLBACKS: dict[str, str] = {
    "grus_grus": "https://raw.githubusercontent.com/bbecquet/bird-tracking/master/data/grus_grus.geojson",
    "ciconia_ciconia": "https://raw.githubusercontent.com/bbecquet/bird-tracking/master/data/ciconia_ciconia.geojson",
    "ciconia_nigra": "https://raw.githubusercontent.com/bbecquet/bird-tracking/master/data/ciconia_nigra.geojson",
}

SESSION = requests.Session()

DATA_ROOT_ENV = "BIRD_MIGRATION_DATA_ROOT"


def ensure_birdflow_route(species_code: str, data_root: Path | None = None) -> Path | None:
    species = species_code.lower()
    root = resolve_data_root(os.getenv(DATA_ROOT_ENV)) if data_root is None else data_root
    routes = routes_dir(root)
    target = birdflow_dir(root) / f"{species}.geojson"
    if target.exists():
        return target

    # Fallback: copy from generic routes if present
    legacy = routes / f"{species}.geojson"
    target.parent.mkdir(parents=True, exist_ok=True)
    if legacy.exists():
        shutil.copy2(legacy, target)
        return target

    url = BIRDFLOW_FALLBACKS.get(species) or os.getenv("BIRDFLOW_GEOJSON_URL")
    if not url:
        return None

    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    target.write_bytes(resp.content)
    return target


def ensure_birdcast_tile(date: str, product: str, data_root: Path | None = None) -> Path | None:
    root = resolve_data_root(os.getenv(DATA_ROOT_ENV)) if data_root is None else data_root
    cache_dir = birdcast_tiles_dir(root) / date / product
    cache_dir.mkdir(parents=True, exist_ok=True)
    expected = cache_dir / "preview.geojson"
    if expected.exists():
        return expected

    # Minimal placeholder using public BirdCast API (returns JSON list)
    url = f"https://birdcast.info/api/v1/migration/summary/{date}"
    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    expected.write_text(resp.text, encoding="utf-8")
    return expected
