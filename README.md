# migration-mcp · Explore Bird Migration with MCP Agents

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](pyproject.toml)
[![CI](https://github.com/Three-Little-Birds/migration-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Three-Little-Birds/migration-mcp/actions/workflows/ci.yml)

`migration-mcp` turns migration datasets into a friendly playground for analysts, educators, and MCP agents. It can synthesise surrogate routes when no data exists, load cached BirdFlow/BirdCast tracks when available, and expose everything through FastAPI or python-sdk tools.

## What you will learn

- How the package organises migration datasets on disk.
- How to request a route (real or surrogate) and visualise it on a map.
- How to give an MCP assistant access to species data, tiles, and cache refresh commands.

## Quick glossary

- **Routes directory** – GeoJSON files stored under `~/bird-data/migration/routes/` by default.
- **BirdFlow cache** – probabilistic routes (GeoJSON) placed in `migration/routes/birdflow/`.
- **BirdCast tiles** – nightly density imagery stored in `migration/tiles/birdcast/`.

## Step 0 – Prepare or fetch data (optional)

The package works even without real data. When no files are found it generates a smooth surrogate path. To use actual routes:

```bash
# Example: download a sample route
mkdir -p ~/bird-data/migration/routes
curl -L -o ~/bird-data/migration/routes/comswi.geojson \
  https://raw.githubusercontent.com/bbecquet/bird-tracking/master/data/comswi.geojson
```

Set up BirdCast tiles similarly, or let the `/admin/refresh` endpoint fetch placeholders.

## Step 1 – Install the package

```bash
uv pip install "git+https://github.com/Three-Little-Birds/migration-mcp.git"
```

## Step 2 – Generate a route in Python

```python
from migration_mcp import RouteRequest, generate_routes

request = RouteRequest(species_code="comswi", num_waypoints=40)
response = generate_routes(request)

print("Status:", response.metadata["status"])
print("First coordinate:", response.geojson["features"][0]["geometry"]["coordinates"][0])
```

If `comswi.geojson` exists, the library resamples it to 40 waypoints. Otherwise it synthesises a smooth flight path using the default scenario settings.

## Step 3 – Visualise with deck.gl or Leaflet

The response contains a ready-to-plot deck.gl payload:

```python
import pandas as pd

track = response.deckgl[0]
df = pd.DataFrame(track["path"], columns=["lon", "lat"])
print(df.head())
```

You can drop `track` into a TripsLayer in React or a Jupyter notebook. The metadata block records the data source, species code, and cache location for reproducibility.

## Step 4 – Expose migration data to MCP agents

### FastAPI service

```python
from migration_mcp.fastapi_app import create_app

app = create_app()
```

Run it locally:

```bash
uv run uvicorn migration_mcp.fastapi_app:create_app --factory --port 8006
```

Endpoints available:

- `POST /routes` – return GeoJSON + deck.gl arrays.
- `GET /datasets` – list cached species routes.
- `GET /tiles` – list BirdCast tiles.
- `POST /admin/refresh` – pull BirdFlow/BirdCast data (protect with `X-MCP-Admin-Token`).

### python-sdk tool

```python
from mcp.server.fastmcp import FastMCP
from migration_mcp.tool import build_tool

mcp = FastMCP("migration-mcp", "Migration route planner")
build_tool(mcp)

if __name__ == "__main__":
    mcp.run()
```

Ask your MCP-aware agent questions like “show me a surrogate route with 60 waypoints for species XYZ” or “refresh the crane dataset”.

## Stretch ideas

- **Classroom exercise:** give students a few species codes and let them compare seasonal routes using the deck.gl output.
- **UAV rehearsal:** combine this tool with ctrltest-mcp to plan control tests around peak migration intensity.
- **Data stewardship:** hook `/admin/refresh` into a cron job so caches stay current.

## Contributing & testing

```bash
uv pip install --system -e .[dev]
uv run ruff check .
uv run pytest
```

Tests provide stubbed datasets so you can experiment without downloading gigabytes of telemetry.

## License

MIT — see [LICENSE](LICENSE).
