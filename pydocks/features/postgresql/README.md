# PostgreSQL

## Purpose

Provides async pytest fixtures that start a real PostgreSQL instance in Docker, wait until the database accepts connections, and tear down containers after tests.

## Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `postgresql_container` | function | Fresh container per test |
| `postgresql_container_session` | session | Shared container across tests in the session |
| `postgresql_clean_all_containers` | session | Removes leftover `test-postgresql*` containers |

## Configuration

Override the Docker image with the `TEST_POSTGRESQL_DOCKER_IMAGE` environment variable.

Default image: `docker.io/postgres:18-alpine`

## Connection

The container exposes PostgreSQL on a dynamic host port. Use `postgresql_container.port` (mapped from container port 5432). Default credentials: user `postgres`, password `postgres`, database `postgres`.

## Example

```python
import asyncpg
import pytest

@pytest.mark.asyncio
async def test_query(postgresql_container):
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=postgresql_container.port,
        user="postgres",
        password="postgres",
        database="postgres",
    )
    try:
        assert await conn.fetchval("SELECT 1") == 1
    finally:
        await conn.close()
```

## Key files

- `postgresql.py` — fixture implementation
- `tests/test_postgresql.py` — integration tests
