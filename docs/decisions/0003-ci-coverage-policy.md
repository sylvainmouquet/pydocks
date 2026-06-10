# ADR 0003: CI coverage policy

## Status

Accepted

## Context

The project targets 100% test coverage for production code. CI must collect coverage on every run, surface results on pull requests, and prevent regressions.

## Decision

1. **Tooling:** Use `pytest-cov` (dev dependency) with `[tool.coverage.*]` configuration in `pyproject.toml`.
2. **Local and CI entry point:** `just test-cov` runs integration tests under `tests/` and `pydocks/features/` with coverage for the `pydocks` package.
3. **Threshold:** CI enforces **100%** line coverage via `COVERAGE_FAIL_UNDER` (default). Tests run under `coverage run` for accurate measurement.
4. **CI reporting:**
   - Markdown coverage summary in the GitHub Actions job summary (`irongut/CodeCoverageSummary`)
   - Pull request comment via `py-cov-action/python-coverage-comment-action` (Python 3.14 matrix job)
   - `coverage.xml` and `htmlcov/` uploaded as workflow artifacts
5. **Scope:** `just test` runs tests without the coverage gate for faster local iteration.

## Consequences

- Coverage regressions fail CI on every matrix Python version.
- Pull requests show line-level coverage without external services.
- Developers use `just test-cov` before opening PRs that touch production code.
