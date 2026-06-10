# Ubuntu

## Purpose

Provides async pytest fixtures that start a minimal Ubuntu container in Docker for shell-based or generic integration tests.

## Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `ubuntu_container` | function | Fresh container per test |
| `ubuntu_container_session` | session | Shared container across tests in the session |
| `ubuntu_clean_all_containers` | session | Removes leftover `test-ubuntu*` containers |

## Configuration

Override the Docker image with the `TEST_UBUNTU_DOCKER_IMAGE` environment variable.

Default image: `docker.io/ubuntu:24.04`

## Usage

The container runs with a long-lived sleep command. Use the pycontainers API on the yielded container object to execute commands inside it.

## Key files

- `ubuntu.py` — fixture implementation
- `tests/test_ubuntu.py` — integration tests
