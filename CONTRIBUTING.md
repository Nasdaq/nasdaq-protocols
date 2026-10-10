# Contributing to nasdaq-protocols

Thanks for your interest in contributing! 🎉

## Development setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management, building,
testing, linting and documentation.

```bash
git clone https://github.com/Nasdaq/nasdaq-protocols.git
cd nasdaq-protocols
uv sync --group dev
```

## Before opening a pull request

Please make sure the following pass locally -- these are the same checks run by CI
(`.github/workflows/wf-push.yml`):

```bash
# Lint
uv run --group lint pylint --fail-under=10.0 "--ignore-patterns=.*egg-info.*,.*test.*" src/*

# Tests (97% coverage required)
uv run --group test pytest --cov=src --cov-fail-under=97

# Build the package
uv build

# Build the docs
cd docs && uv run --group docs make html
```

## Guidelines

- All existing tests must pass; add new tests for new behavior.
- Pylint must report 10/10.
- Code should be documented, with docstrings added where needed.
- User-facing changes should be documented in the relevant file under `docs/` and noted in
  [CHANGELOG.md](CHANGELOG.md) under `[Unreleased]`.

## Documentation

Documentation source lives under `docs/` as Markdown (built with
[Sphinx](https://www.sphinx-doc.org/) + [MyST](https://myst-parser.readthedocs.io/)) and is
published automatically to [GitHub Pages](https://nasdaq.github.io/nasdaq-protocols/) on
every push to `main`. See the
[Developer's Guide](https://nasdaq.github.io/nasdaq-protocols/developer_guide.html) for more
detail.

## Reporting issues

Please use the [issue tracker](https://github.com/Nasdaq/nasdaq-protocols/issues) and
include a minimal reproduction where possible.
