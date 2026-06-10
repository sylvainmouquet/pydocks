# OpenTofu

## Purpose

Provides async pytest fixtures that start an OpenTofu container with a mounted Terraform workspace, wait until the workspace is ready, and tear down containers after tests.

## Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `opentofu_container` | function | Fresh container per test |
| `opentofu_container_session` | session | Shared container across tests in the session |
| `opentofu_clean_all_containers` | session | Removes leftover `test-opentofu*` containers |

## Configuration

Override the Docker image with the `TEST_OPENTOFU_DOCKER_IMAGE` environment variable.

Default image: `ghcr.io/opentofu/opentofu:1.9`

## Resources

The feature mounts `resources/` (including `main.tf` and a `ready` marker file) at `/terraform` inside the container. Readiness is determined by the presence of the `ready` file after initialization.

## Key files

- `opentofu.py` — fixture implementation
- `resources/` — Terraform workspace and readiness marker
- `tests/test_opentofu.py` — integration tests
