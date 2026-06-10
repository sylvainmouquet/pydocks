# PyDocks Architecture

## Overview

PyDocks is a pytest plugin that provides Docker container fixtures for integration tests. The codebase follows a **feature-based** layout: each container type is a self-contained feature, and cross-cutting Docker utilities live in shared infrastructure.

## Layout

```text
pydocks/
├── __init__.py                 # Public API and pytest plugin entry point
├── features/
│   ├── alpine/
│   │   ├── alpine.py           # Fixtures and setup logic
│   │   ├── resources/          # Feature-specific assets (when needed)
│   │   └── tests/
│   ├── postgresql/
│   ├── redis/
│   ├── valkey/
│   ├── vault/
│   ├── ubuntu/
│   └── opentofu/
└── shared/
    └── infrastructure/
        └── plugin.py           # Docker session fixture and helpers
```

## Major components

| Component | Role |
|-----------|------|
| `pydocks/__init__.py` | Registers fixtures with pytest and exposes the public API |
| `features/<name>/` | Owns container image config, fixtures, resources, and tests |
| `shared/infrastructure/plugin.py` | Session-scoped `docker` fixture, cleanup, port checks |

## Data flow

1. Pytest loads the `pydocks` entry point (`pyproject.toml` → `pytest11`).
2. The session-scoped `docker` fixture provides a `PyContainers` client.
3. Feature fixtures start containers, wait for readiness, yield the instance, then tear down.
4. Tests import fixtures by name (e.g. `postgresql_container`) without knowing the internal layout.

## Dependencies

- **pytest / pytest-asyncio** — fixture lifecycle and async tests
- **pycontainers** — Docker API wrapper
- **reattempt** — retry helpers for connection readiness
- **anyio** — async socket I/O

## Adding a new container feature

1. Create `pydocks/features/<name>/` with implementation, optional `resources/`, and `tests/`.
2. Export fixtures from `pydocks/features/<name>/__init__.py`.
3. Register fixtures in `pydocks/__init__.py` (`__all__` and imports).
