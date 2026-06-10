# Redis

## Purpose

Provides async pytest fixtures that start a real Redis instance in Docker, wait until the server accepts connections, and tear down containers after tests.

## Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `redis_container` | function | Fresh container per test |
| `redis_container_session` | session | Shared container across tests in the session |
| `redis_clean_all_containers` | session | Removes leftover `test-redis*` containers |

## Configuration

Override the Docker image with the `TEST_REDIS_DOCKER_IMAGE` environment variable.

Default image: `docker.io/redis:7.4.1`

## Connection

The container exposes Redis on a dynamic host port. Use `redis_container.port` (mapped from container port 6379).

## Example

```python
import pytest
from redis import asyncio as aioredis

@pytest.mark.asyncio
async def test_ping(redis_container):
    client = aioredis.Redis(host="127.0.0.1", port=redis_container.port)
    try:
        assert await client.ping()
    finally:
        await client.aclose()
```

## Key files

- `redis.py` — fixture implementation
- `tests/test_redis.py` — integration tests
