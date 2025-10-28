# migration-mcp

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-brightgreen.svg)](pyproject.toml)
[![CI](https://github.com/yevheniikravchuk/migration-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/yevheniikravchuk/migration-mcp/actions/workflows/ci.yml)

Migration route synthesis toolkit for Model Context Protocol agents. It generates surrogate trajectories and pulls cached BirdFlow/BirdCast datasets when available.

## Features
- Pydantic models for species-aware route requests and responses.
- Helper to synthesize deck.gl-ready paths when no real dataset is present.
- FastAPI app factory and python-sdk tool integration.

## Installation
```bash
pip install "git+https://github.com/yevheniikravchuk/migration-mcp.git"
```

## Usage
```python
from migration_mcp import RouteRequest, generate_routes

response = generate_routes(
    RouteRequest(
        species_code="comswi",
        num_waypoints=20,
        cruise_velocity_m_s=11.0,
        trim_yaw_rad=0.15,
        climb_rate_m_s=0.2,
    )
)
print(response.geojson)
```

## Development
```bash
uv pip install --system -e .[dev]
uv run ruff check .
uv run pytest
```

## License
MIT — see [LICENSE](LICENSE).
