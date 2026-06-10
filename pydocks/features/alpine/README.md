# Alpine

## Purpose

Provides async pytest fixtures that start a minimal Alpine Linux container in Docker for lightweight shell-based integration tests.

## Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `alpine_container` | function | Fresh container per test |
| `alpine_container_session` | session | Shared container across tests in the session |
| `alpine_clean_all_containers` | session | Removes leftover `test-alpine*` containers |

## Configuration

Override the Docker image with the `TEST_ALPINE_DOCKER_IMAGE` environment variable.

Default image: `docker.io/alpine:3.19`

## Usage

The container runs with a long-lived sleep command. Use the pycontainers API on the yielded container object to execute commands inside it.

## Key files

- `alpine.py` — fixture implementation
- `tests/test_alpine.py` — integration tests
