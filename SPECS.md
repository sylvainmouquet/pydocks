# PyDocks — Product Specification

PyDocks is a pytest plugin that provides Docker container fixtures for integration tests. Each supported service exposes function- and session-scoped fixtures plus a cleanup helper, so tests can spin up real dependencies without managing Docker lifecycle by hand.

## High impact, relatively simple

### 1. PostgreSQL container fixtures

**Status:** Done

Async pytest fixtures for PostgreSQL with port allocation, readiness checks, and automatic teardown.

- [x] Function-scoped `postgresql_container` fixture
- [x] Session-scoped `postgresql_container_session` fixture
- [x] `postgresql_clean_all_containers` cleanup helper
- [x] Port availability wait before container start

**Key files:** `pydocks/features/postgresql/postgresql.py`, `tests/test_postgresql.py`

---

### 2. Redis container fixtures

**Status:** Done

Async pytest fixtures for Redis with the standard function/session/cleanup trio.

- [x] Function-scoped `redis_container` fixture
- [x] Session-scoped `redis_container_session` fixture
- [x] `redis_clean_all_containers` cleanup helper

**Key files:** `pydocks/features/redis/redis.py`, `tests/test_redis.py`

---

### 3. Valkey container fixtures

**Status:** Done

Async pytest fixtures for Valkey (Redis-compatible) with the standard function/session/cleanup trio.

- [x] Function-scoped `valkey_container` fixture
- [x] Session-scoped `valkey_container_session` fixture
- [x] `valkey_clean_all_containers` cleanup helper

**Key files:** `pydocks/features/valkey/valkey.py`, `tests/test_valkey.py`

---

### 4. Hashicorp Vault container fixtures

**Status:** Done

Async pytest fixtures for Vault with initialization scripts and readiness checks.

- [x] Function-scoped `vault_container` fixture
- [x] Session-scoped `vault_container_session` fixture
- [x] `vault_clean_all_containers` cleanup helper

**Key files:** `pydocks/features/vault/vault.py`, `pydocks/vault_resources/`, `tests/test_vault.py`

---

### 5. Shared Docker infrastructure

**Status:** Done

Session-scoped Docker client, connection helpers, and container lifecycle utilities shared by all features.

- [x] Session-scoped `docker` fixture (CI, Colima, and local socket support)
- [x] `socket_test_connection` and `wait_port_available` helpers
- [x] `clean_containers` and `wait_and_run_container` utilities

**Key files:** `pydocks/shared/infrastructure/plugin.py`

## Medium impact — broadens scope

### 6. Ubuntu container fixtures

**Status:** Done

Generic Ubuntu base image fixtures for shell-level integration tests.

- [x] Function-scoped `ubuntu_container` fixture
- [x] Session-scoped `ubuntu_container_session` fixture
- [x] `ubuntu_clean_all_containers` cleanup helper
- [x] Configurable sleep time for long-running commands

**Key files:** `pydocks/features/ubuntu/ubuntu.py`, `tests/test_ubuntu.py`

---

### 7. Alpine container fixtures

**Status:** Done

Lightweight Alpine base image fixtures for minimal container tests.

- [x] Function-scoped `alpine_container` fixture
- [x] Session-scoped `alpine_container_session` fixture
- [x] `alpine_clean_all_containers` cleanup helper

**Key files:** `pydocks/features/alpine/alpine.py`, `tests/test_alpine.py`

---

### 8. OpenTofu container fixtures

**Status:** Done

Async pytest fixtures for OpenTofu/Terraform-style infrastructure tests inside a container.

- [x] Function-scoped `opentofu_container` fixture
- [x] Session-scoped `opentofu_container_session` fixture
- [x] `opentofu_clean_all_containers` cleanup helper
- [x] Bundled example Terraform resources

**Key files:** `pydocks/features/opentofu/opentofu.py`, `pydocks/features/opentofu/resources/`, `pydocks/opentofu_resources/`, `tests/test_opentofu.py`

---

### 9. Feature-based architecture (v2)

**Status:** Done

Reorganize the codebase by container capability instead of flat module layout, without breaking the public fixture API.

- [x] Move container modules under `pydocks/features/<name>/`
- [x] Extract shared Docker helpers to `pydocks/shared/infrastructure/`
- [x] Register pytest plugin entry point unchanged (`pydocks` → `pydocks/__init__.py`)
- [x] Document layout in `docs/architecture.md`
- [ ] Co-locate tests under `pydocks/features/<name>/tests/`
- [ ] Consolidate legacy resource paths (`vault_resources/`, `opentofu_resources/`)

**Key files:** `pydocks/__init__.py`, `pydocks/features/`, `pydocks/shared/infrastructure/plugin.py`, `docs/architecture.md`

## Polish & UX

### 10. Justfile task runner

**Status:** Done

Replace Makefile with `justfile` as the single source of truth for development commands.

- [x] `just install`, `just test`, `just lint`, `just check`, `just build`
- [x] Docker availability check via `check-docker` recipe (Colima on macOS)
- [x] CI workflows invoke `just install` and `just test`

**Key files:** `justfile`, `.github/actions/test/action.yml`

---

### 11. Pytest plugin registration

**Status:** Done

Zero-config fixture discovery when PyDocks is installed as a dependency.

- [x] `pytest11` entry point in `pyproject.toml`
- [x] Public `__all__` exports for all fixtures
- [x] Async mode configured via `pytest.ini`

**Key files:** `pyproject.toml`, `pydocks/__init__.py`, `pytest.ini`

---

### 12. CI on Ubuntu (multi-Python)

**Status:** Done

Run the full test suite on Ubuntu across Python 3.10–3.14 on every push and pull request.

- [x] GitHub Actions workflow with Python version matrix
- [x] Composite test action (uv, just, Docker host mapping)

**Key files:** `.github/workflows/test.yml`, `.github/actions/test/action.yml`

## New Opportunities

### 13. Additional container types

**Status:** Planned

Expand coverage for other common integration-test dependencies.

- [ ] MongoDB fixtures
- [ ] MySQL/MariaDB fixtures
- [ ] Kafka or NATS fixtures

**Potential files:** `pydocks/features/mongodb/`, `pydocks/features/mysql/`, `pydocks/features/kafka/`

---

### 14. macOS and Windows CI

**Status:** Planned

Re-enable cross-platform CI jobs currently commented out in the workflow.

- [ ] macOS matrix (Python 3.10–3.14)
- [ ] Windows matrix (Python 3.10–3.14)
- [ ] Document platform-specific Docker setup

**Potential files:** `.github/workflows/test.yml`, `.github/actions/test/action.yml`

---

### 15. Coverage enforcement

**Status:** Done

Collect and enforce test coverage in CI per project policy (100% target).

- [x] Add `pytest-cov` to dev dependencies
- [x] Configure coverage threshold in CI
- [x] Publish coverage summary on pull requests

**Key files:** `pyproject.toml`, `.github/workflows/test.yml`, `.github/actions/test/action.yml`, `justfile`, `docs/decisions/0003-ci-coverage-policy.md`

---

### 16. Published documentation site

**Status:** Done

Generate and publish long-form docs via GitHub Pages using MkDocs Material.

- [x] Choose doc generator (MkDocs Material)
- [x] GitHub Actions workflow to build and publish `docs/`
- [x] Feature-level README files under `pydocks/features/<name>/`

**Key files:** `mkdocs.yml`, `docs/`, `.github/workflows/docs.yml`, `pydocks/features/*/README.md`, `justfile`

## Recommended Roadmap

1. **Finish v2 migration** — co-locate tests and remove legacy resource directories.
2. **Release 2.0.0** — add `CHANGELOG.md`, tag, and publish to PyPI.
3. **Cross-platform CI** — restore macOS and Windows jobs.
4. **New containers** — add high-demand services (MongoDB, MySQL) based on user requests.

## Architecture notes

PyDocks follows a **feature-based** layout: each container type owns its fixtures, optional resources, and (eventually) tests. Cross-cutting Docker utilities live in `shared/infrastructure/`.

```text
pydocks/
├── __init__.py                 # Public API and pytest plugin entry point
├── features/
│   ├── alpine/
│   ├── opentofu/
│   ├── postgresql/
│   ├── redis/
│   ├── ubuntu/
│   ├── valkey/
│   └── vault/
└── shared/
    └── infrastructure/
        └── plugin.py           # Session docker fixture and helpers
```

**Data flow:**

1. Pytest loads the `pydocks` entry point (`pyproject.toml` → `pytest11`).
2. The session-scoped `docker` fixture provides a `PyContainers` client.
3. Feature fixtures start containers, wait for readiness, yield the instance, then tear down.
4. Tests import fixtures by name (e.g. `postgresql_container`) without knowing internal paths.

**Dependencies:** pytest, pytest-asyncio, pycontainers, reattempt, anyio.

See [docs/architecture.md](docs/architecture.md) for the extension guide when adding a new container feature.
