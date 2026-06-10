# PyDocks

PyDocks is a group of pytest fixures for running tests with Docker containers

### Demonstration:

```python
import pytest
import asyncpg

@pytest.mark.asyncio
async def test_postgresql_execute_command(postgresql_container):
    # Connect to the PostgreSQL database
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=5433,
        user="postgres",
        password="postgres",
        database="postgres",
    )

    try:
        # Execute a simple command
        result = await conn.fetchval("SELECT 1")
        assert result == 1, "Failed to execute command on PostgreSQL"
    finally:
        # Close the connection
        await conn.close()

```

## Table of Contents

- [PyDocks](#PyDocks)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Installation](#installation)
  - [Development](#development)
  - [Usage](#usage)
  - [License](#license)
  - [Contact](#contact)

## Description

PyDocks is a Python library that provides a set of pytest fixtures for running tests with Docker containers. It simplifies the process of setting up, managing, and tearing down Docker containers during test execution.

Key features include:
- Easy integration with pytest
- Support for PostgreSQL, Hashicorp Vault, Redis, Valkey, and more
- Automatic container cleanup
- Configurable container settings
- Reusable session-scoped containers for improved test performance

PyDocks is designed to make testing with Docker containers more efficient and less error-prone, allowing developers to focus on writing tests rather than managing infrastructure.

## Installation

```bash
# Install the dependency
pip install pydocks
uv add pydocks
poetry add pydocks
```

## Documentation

- [Product specification](SPECS.md) — feature status and roadmap
- [Architecture](docs/architecture.md) — feature-based layout and extension guide
- [CI coverage policy](docs/decisions/0003-ci-coverage-policy.md) — threshold and reporting

## Development

Install [just](https://github.com/casey/just) and [uv](https://docs.astral.sh/uv/), then:

```bash
just install    # install dependencies
just test       # run tests (no coverage gate)
just test-cov   # run tests with 100% coverage enforcement
just coverage   # show coverage report from the last test-cov run
just lint       # run linter and formatter
just check      # run pyright
just --list     # list all recipes
```

Tests collect coverage via `just test-cov`, which fails if line coverage drops below 100%. CI runs the same recipe, publishes a coverage summary in the job output, posts a comment on pull requests, and uploads `coverage.xml` / HTML reports as workflow artifacts.

## Usage

### Remove all old containers
```python
import logging
import pytest
import pytest_asyncio

logger = logging.getLogger(__name__)

@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def begin_clean_all_containers(postgresql_clean_all_containers):
    logger.info(
        "Beginning container cleanup session",
        extra={"feature": "postgresql"},
    )
```

### Use a function container
```python
import pytest

@pytest.mark.asyncio
async def test_postgresql_execute_command(postgresql_container):
  ...
```

### Use a session container, to keep the container to use it in multiple tests
```python
import pytest

@pytest.mark.asyncio(loop_scope="session")
async def test_reuse_postgresql_container_1_2(postgresql_container_session):
  ...
  # postgresql_container_session creates a new container

@pytest.mark.asyncio(loop_scope="session")
async def test_reuse_postgresql_container_2_2(postgresql_container_session):
  ...
  # postgresql_container_session uses the same instance of container created in test_reuse_postgresql_container_1_2
```

### Available Containers

PyDocks provides fixtures for the following Docker containers:

- **PostgreSQL**: `postgresql_container`, `postgresql_container_session`, `postgresql_clean_all_containers`
- **Redis**: `redis_container`, `redis_container_session`, `redis_clean_all_containers`
- **Valkey**: `valkey_container`, `valkey_container_session`, `valkey_clean_all_containers`
- **Hashicorp Vault**: `vault_container`, `vault_container_session`, `vault_clean_all_containers`
- **Ubuntu**: `ubuntu_container`, `ubuntu_container_session`, `ubuntu_clean_all_containers`
- **Alpine**: `alpine_container`, `alpine_container_session`, `alpine_clean_all_containers`
- **OpenTofu**: `opentofu_container`, `opentofu_container_session`, `opentofu_clean_all_containers`

## License

PyDocks is released under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For questions, suggestions, or issues related to PyDocks, please open an issue on the GitHub repository.