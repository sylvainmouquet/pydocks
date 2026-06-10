# Hashicorp Vault

## Purpose

Provides async pytest fixtures that start a Vault dev-mode instance in Docker with bundled init scripts, wait until the API is reachable, and tear down containers after tests.

## Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `vault_container` | function | Fresh container per test |
| `vault_container_session` | session | Shared container across tests in the session |
| `vault_clean_all_containers` | session | Removes leftover `test-vault*` containers |

## Configuration

Override the Docker image with the `TEST_VAULT_DOCKER_IMAGE` environment variable.

Default image: `docker.io/hashicorp/vault:1.18`

## Connection

The container exposes the Vault API on a dynamic host port. Use `vault_container.port` (mapped from container port 8200). The dev root token is `00000000-0000-0000-0000-000000000000`.

## Resources

The feature mounts `resources/test-vault-init.sh` and `resources/vault-test.json` into the container for initialization.

## Key files

- `vault.py` — fixture implementation
- `resources/` — init script and Vault configuration
- `tests/test_vault.py` — integration tests
