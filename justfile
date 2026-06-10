python_version := env_var_or_default('PYTHON_VERSION', '3.14')

set shell := ["bash", "-euc"]
set positional-arguments

# List available recipes
default:
    @just --list

# Commit and push work in progress
wip:
    git add .
    git commit -m "WIP: Work in progress"
    git push

# Install dependencies
install:
    uv sync --python {{python_version}} --all-extras --dev

# Ensure VERSION is set before building
check-version:
    #!/usr/bin/env bash
    if [ -z "${VERSION:-}" ]; then
      echo "VERSION is not set. Please set the VERSION environment variable."
      exit 1
    fi

# Build the project (requires VERSION)
build: check-version
    rm -rf dist/* || true
    ./scripts/version.sh "${VERSION}"
    @cat pyproject.toml | grep version
    @cat pydocks/__init__.py | grep version
    uv build --python {{python_version}}

# Run pyright type checker
check:
    echo "Run pyright"
    PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright

# Ensure Docker is available locally (starts Colima on macOS)
check-docker:
    #!/usr/bin/env bash
    echo "check-docker"
    if [ -z "${CI:-}" ]; then
      echo "ci is not set"
      if [ "$(uname)" = "Darwin" ]; then
        which colima &>/dev/null || echo "You must install colima"
        docker info > /dev/null 2>&1 || colima stop
        docker info > /dev/null 2>&1 || colima start --cpu 4 --memory 12
      else
        echo "docker must be started"
      fi
    fi

# Upload build artifacts to PyPI
deploy:
    uvx twine upload dist/*

# Install the local wheel
install-local:
    pip3 install dist/*.whl

# Run tests (optional pytest args: just test tests/test_foo.py)
test *args: check-docker
    #!/usr/bin/env bash
    if [ $# -eq 0 ]; then
      uv run --python {{python_version}} pytest -vvv --log-cli-level=INFO
    else
      uv run --python {{python_version}} pytest -vvv --log-cli-level=INFO "$@"
    fi

# Run tests with coverage collection and 100% threshold enforcement
test-cov *args: check-docker
    #!/usr/bin/env bash
    set -euo pipefail
    COVERAGE_FAIL_UNDER="${COVERAGE_FAIL_UNDER:-100}"
    if [ $# -eq 0 ]; then
      uv run --python {{python_version}} coverage run -m pytest -vvv --log-cli-level=INFO
    else
      uv run --python {{python_version}} coverage run -m pytest -vvv --log-cli-level=INFO "$@"
    fi
    uv run coverage report --fail-under="${COVERAGE_FAIL_UNDER}"
    uv run coverage html
    uv run coverage xml -o coverage.xml

# Show coverage report from the last test-cov run
coverage:
    uv run --python {{python_version}} coverage report --show-missing

# Run linter and formatter
lint:
    uv run ruff check --fix
    uv run ruff format
    uv run ruff format --check

# Upgrade and sync dependencies
update:
    uv lock --upgrade
    uv sync

# List outdated dependencies
check-deps:
    .venv/bin/pip list --outdated
