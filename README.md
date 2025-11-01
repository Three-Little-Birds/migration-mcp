# migration-mcp - Probabilistic bird routes for MCP agents

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-3776AB.svg" alt="Python 3.10 or newer"></a>
  <a href="https://github.com/Three-Little-Birds/migration-mcp/actions/workflows/ci.yml"><img src="https://github.com/Three-Little-Birds/migration-mcp/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <img src="https://img.shields.io/badge/status-stable-4caf50.svg" alt="Project status: stable">
  <img src="https://img.shields.io/badge/MCP-tooling-blueviolet.svg" alt="MCP tooling badge">
</p>

> **TL;DR**: Serve BirdFlow/BirdCast/sideloaded GeoJSON routes through MCP so agents can visualise, score, and rehearse migration profiles.

## Table of contents

1. [Why agents love it](#why-agents-love-it)
2. [Quickstart](#quickstart)
3. [Run as a service](#run-as-a-service)
4. [Agent playbook](#agent-playbook)
5. [Stretch ideas](#stretch-ideas)
6. [Accessibility & upkeep](#accessibility--upkeep)
7. [Contributing](#contributing)

## Why agents love it

| Persona | Immediate value | Longer-term payoff |
|---------|-----------------|--------------------|
| **Data explorers** | Query cached BirdFlow/BirdCast routes or drop in GeoJSON to get deck.gl-ready outputs. | Metadata captures species, status, and provenance for dashboards. |
| **Decision-support teams** | Merge probabilistic routes with perception/control scenarios through MCP. | Caching + refresh scripts make it easy to maintain nightly datasets in CI.

## Quickstart

```bash
uv pip install "git+https://github.com/Three-Little-Birds/migration-mcp.git"
```

Populate sample routes:

```bash
uv run python scripts/data/refresh_migration_sources.py --data-root ~/bird-data
```

Query from Python:

```python
from migration_mcp import RouteRequest, generate_routes

request = RouteRequest(num_waypoints=20, species_code="comswi")
response = generate_routes(request)
print(response.metadata)
```

## Run as a service

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

## Accessibility & upkeep

- Concise badges with alt text keep the hero section readable while signalling status at a glance.
- Tests mock dataset layers; run `uv run pytest` before shipping.
- Respect data licences-document the origin (BirdFlow, BirdCast, GeoJSON) when expanding caches.

## Contributing

1. `uv pip install --system -e .[dev]`
2. `uv run ruff check .` and `uv run pytest`
3. Include sample GeoJSON snippets in PRs so reviewers can validate deck.gl output.

MIT license - see [LICENSE](LICENSE).
