SHELL:=/bin/bash

SUPPORTED_COMMANDS := test
SUPPORTS_MAKE_ARGS := $(findstring $(firstword $(MAKECMDGOALS)), $(SUPPORTED_COMMANDS))
ifneq "$(SUPPORTS_MAKE_ARGS)" ""
  COMMAND_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  COMMAND_ARGS := $(subst :,\:,$(COMMAND_ARGS))
  $(eval $(COMMAND_ARGS):;@:)
endif

# Git workflow commands
.PHONY: wip
wip:
	git add .
	git commit -m "WIP: Work in progress"
	git push

# Install command
.PHONY: install
install:
	uv sync --python $${PYTHON_VERSION:-3.13} --all-extras --dev
	
# Build command
.PHONY: build
build: check-version
	rm -rf dist/* || true
#	ls -al
	./scripts/version.sh "${VERSION}"
	@cat pyproject.toml | grep version
	@cat pydocks/__init__.py | grep version
	uv build --python $${PYTHON_VERSION:-3.13}

.PHONY: check-version
check-version:
	@if [ -z "${VERSION}" ]; then \
		echo "VERSION is not set. Please set the VERSION environment variable."; \
		exit 1; \
	fi

.PHONY: check
check: 
	echo "Run pyright"
	PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright

.PHONY: check-docker
check-docker:
	echo "check-docker"
ifeq ($(strip $(CI)),)
	echo "ci is not set"
ifeq ($(shell uname),Darwin)
# we use colima in MacOs
		which colima &>/dev/null  || echo "You must install colima"
		docker info > /dev/null 2>&1 || colima stop
		docker info > /dev/null 2>&1 || colima start --cpu 4 --memory 12
else
	echo "docker must be started"
endif
endif

# Deploy command
.PHONY: deploy
deploy:
	uvx twine upload dist/*

# Install local build command
.PHONY: install-local
install-local:
	pip3 install dist/*.whl

# Test command
.PHONY: test
test: check-docker
	@echo "Modified arguments: $(new_args)"
	@if [ -z "$(COMMAND_ARGS)" ]; then \
		uv run --python $${PYTHON_VERSION:-3.13} pytest -v --log-cli-level=INFO; \
	else \
		uv run --python $${PYTHON_VERSION:-3.13} pytest -v --log-cli-level=INFO $(new_args); \
	fi

# Lint command
.PHONY: lint
lint:
	uv run ruff check --fix
	uv run ruff format
	uv run ruff format --check


# Update dependencies
.PHONY: update
update:
	uv lock --upgrade
	uv sync

# Check for outdated dependencies
.PHONY: check-deps
check-deps:
	.venv/bin/pip list --outdated

# Display all available commands
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  wip           - Commit and push work in progress"
	@echo "  install       - Install dependencies"
	@echo "  build         - Build the project"
	@echo "  deploy        - Deploy the project"
	@echo "  install-local - Install the build locally"
	@echo "  update        - Update dependencies"
	@echo "  check-deps    - Check for outdated dependencies"
	@echo "  test          - Run tests"
	@echo "  lint          - Run linter"
	@echo "  help          - Display this help message"
