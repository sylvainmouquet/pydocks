# Valkey

## Purpose

Provides async pytest fixtures that start a real Valkey instance (Redis-compatible) in Docker, wait until the server accepts connections, and tear down containers after tests.

## Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `valkey_container` | function | Fresh container per test |
| `valkey_container_session` | session | Shared container across tests in the session |
| `valkey_clean_all_containers` | session | Removes leftover `test-valkey*` containers |

## Configuration

Override the Docker image with the `TEST_VALKEY_DOCKER_IMAGE` environment variable.

Default image: `docker.io/valkey/valkey:8.1.1`

## Connection

The container exposes Valkey on a dynamic host port. Use `valkey_container.port` (mapped from container port 6379).

## Example

```python
import pytest
from redis import asyncio as aioredis

@pytest.mark.asyncio
async def test_ping(valkey_container):
    client = aioredis.Redis(host="127.0.0.1", port=valkey_container.port)
    try:
        assert await client.ping()
    finally:
        await client.aclose()
```

## Key files

- `valkey.py` — fixture implementation
- `tests/test_valkey.py` — integration tests
