# PyDocks

PyDocks is a pytest plugin that provides Docker container fixtures for integration tests. Each supported service exposes function- and session-scoped fixtures plus a cleanup helper, so tests can spin up real dependencies without managing Docker lifecycle by hand.

## Quick start

```bash
pip install pydocks
```

```python
import pytest
import asyncpg

@pytest.mark.asyncio
async def test_postgresql_execute_command(postgresql_container):
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

## Available containers

| Feature | Fixtures |
|---------|----------|
| [PostgreSQL](features/postgresql.md) | `postgresql_container`, `postgresql_container_session`, `postgresql_clean_all_containers` |
| [Redis](features/redis.md) | `redis_container`, `redis_container_session`, `redis_clean_all_containers` |
| [Valkey](features/valkey.md) | `valkey_container`, `valkey_container_session`, `valkey_clean_all_containers` |
| [Vault](features/vault.md) | `vault_container`, `vault_container_session`, `vault_clean_all_containers` |
| [Ubuntu](features/ubuntu.md) | `ubuntu_container`, `ubuntu_container_session`, `ubuntu_clean_all_containers` |
| [Alpine](features/alpine.md) | `alpine_container`, `alpine_container_session`, `alpine_clean_all_containers` |
| [OpenTofu](features/opentofu.md) | `opentofu_container`, `opentofu_container_session`, `opentofu_clean_all_containers` |

## Development

Install [just](https://github.com/casey/just) and [uv](https://docs.astral.sh/uv/), then:

```bash
just install
just test-cov
just docs-serve   # preview documentation locally
```

See the [architecture guide](architecture.md) for the feature-based layout and how to add a new container feature.
