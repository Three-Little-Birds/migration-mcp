# migration-mcp - Probabilistic bird routes for MCP agents

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-3776AB.svg" alt="Python 3.10 or newer"></a>
  <a href="https://github.com/Three-Little-Birds/migration-mcp/actions/workflows/ci.yml"><img src="https://github.com/Three-Little-Birds/migration-mcp/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <img src="https://img.shields.io/badge/MCP-tooling-blueviolet.svg" alt="MCP tooling badge">
</p>

> **TL;DR**: Serve BirdFlow/BirdCast/sideloaded GeoJSON routes through MCP so agents can visualise, score, and rehearse migration profiles.

## Table of contents

1. [What it provides](#what-it-provides)
2. [Quickstart](#quickstart)
3. [Run as a service](#run-as-a-service)
4. [Agent playbook](#agent-playbook)
5. [Stretch ideas](#stretch-ideas)
6. [Install & maintenance](#install--maintenance)
7. [Contributing](#contributing)

## What it provides

| Scenario | Value |
|----------|-------|
| BirdFlow routes | Surface origin→destination probabilities from [BirdFlow](https://birdflow-science.github.io/) exports without running R. |
| BirdCast densities | Cache nightly [BirdCast](https://dashboard.birdcast.info/) tiles and list them through MCP for map overlays. |
| Movebank telemetry | Authenticate against [Movebank](https://www.movebank.org/) (when credentials are supplied) and convert event data into simplified GeoJSON tracks. |

## Quickstart

```bash
uv pip install "git+https://github.com/Three-Little-Birds/migration-mcp.git"
```

Populate sample routes:

```bash
PYTHONPATH=. uv run python scripts/data/refresh_migration_sources.py
```

> BirdCast removed the unauthenticated JSON endpoint (`/api/v1/migration/summary/<date>` now responds with HTML 404). Until the partnership API is restored, expect the helper above to log `Failed to refresh BirdCast tile` and stage tiles manually under `~/bird-data/migration/routes/birdcast/` if you have access to the official feeds.

To enable Movebank pulls, store credentials locally (they are not committed):

```bash
uv run python scripts/setup_movebank_credentials.py --login your_movebank_user --password '...' --force
source ~/.config/three-little-birds/movebank.env  # exports MOVEBANK_LOGIN/MOVEBANK_PASSWORD
```

Fetch a licensed dataset once you have accepted the terms on movebank.org:

```bash
uv run python scripts/data/fetch_movebank_study.py \
  --study-id 123456789 \
  --login-file ~/.config/three-little-birds/movebank.env \
  --output ~/bird-data/migration/routes/stork.geojson
```

Query from Python:

```python
from migration_mcp import RouteRequest, generate_routes

request = RouteRequest(num_waypoints=20, species_code="comswi")
response = generate_routes(request)
print(response.metadata["dataset_source"])  # "birdflow" | "birdcast" | "movebank" | "custom"
print(response.geojson["features"][0]["properties"].keys())
```

Example GeoJSON feature:

```json
{
  "type": "Feature",
  "properties": {
    "species": "Grus grus",
    "timestamps": ["2010-09-10T17:00:00Z", "2010-09-28T17:00:00Z", ...],
    "source": "birdflow"
  },
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [-73.98, 40.75, 150.0],
      [-73.12, 41.30, 120.0],
      [-72.45, 42.05, 80.0]
    ]
  }
}
```

### ToolHive smoke test

Ensure `~/bird-data/migration/routes/` (or `MIGRATION_DATA_ROOT`) contains GeoJSON tracks, then run:

```bash
PYTHONPATH=. uvx --with 'mcp==1.20.0' python scripts/integration/run_migration.py
```

## Run as a service

### CLI (STDIO transport)

```bash
uvx migration-mcp  # runs the MCP over stdio
# or python -m migration_mcp
```

Use `python -m migration_mcp --describe` to inspect metadata without launching the server.

### FastAPI (REST)

```bash
uv run uvicorn migration_mcp.fastapi_app:create_app --factory --port 8006
```

### python-sdk tool (STDIO / MCP)

```python
from mcp.server.fastmcp import FastMCP
from migration_mcp.tool import build_tool

mcp = FastMCP("migration-mcp", "Migration route synthesis")
build_tool(mcp)

if __name__ == "__main__":
    mcp.run()
```

## Agent playbook

- **Deck.gl overlays** - feed `response.deckgl` straight into map visualisations.
- **Behaviour modelling** - combine routes with `ctrltest-mcp` to design gust budgets along migratory corridors.
- **Data governance** - exploit metadata to differentiate BirdFlow, BirdCast, or manual GeoJSON sources.

## Stretch ideas

1. Plug Movebank-authenticated pulls into the same cache using the new credential helper.
2. Generate scenario collections and share them with simulation teams via `configs/default_scenario.json` patches.
3. Schedule nightly refreshes to keep BirdCast tiles current.

## Install & maintenance

- **Runtime install:** follow the [Quickstart](#quickstart) `uv pip install "git+https://github.com/Three-Little-Birds/migration-mcp.git"` step on any host that should serve migration data.
- **Data root care:** keep `~/bird-data/migration/` (or `BIRD_MIGRATION_DATA_ROOT`) populated via `scripts/data/refresh_migration_sources.py`, and note the provenance (BirdFlow, BirdCast, Movebank) in PRs.
- **Licensing & access:** BirdFlow routes follow the upstream MIT licence; BirdCast tiles are © Cornell Lab of Ornithology (cite [BirdCast](https://birdcast.info) in derivative works), and Movebank data typically requires explicit approval per study. Configure credentials via `scripts/setup_movebank_credentials.py`, review licences, and only cache datasets you have permission to use.

## Contributing

1. `uv pip install --system -e .[dev]`
2. `uv run ruff check .` and `uv run pytest`
3. Include sample GeoJSON snippets in PRs so reviewers can validate deck.gl output.

MIT license - see [LICENSE](LICENSE).
