(developer-guide)=
# Developer's Guide

This guide is intended for developers who want to contribute to the
development of the `nasdaq-protocols` library.

## Guidelines

Before merging to main, please ensure that the following guidelines are met:

- All existing tests are passing.
- New tests are added when needed.
- Pylint reports no errors, 10/10
- Code is documented and docstrings are added when needed.
- Documentation is included in the markdown files under `docs/`.

## Building

This project uses [uv](https://docs.astral.sh/uv/) for dependency management, builds,
tests, linting and docs -- there is no `tox.ini` at the repo root.

Install the dev dependency group once:

```console
$ uv sync --group dev
```

Then run each step individually:

```console
$ uv run --group lint pylint --fail-under=10.0 "--ignore-patterns=.*egg-info.*,.*test.*" src/*
$ uv run --group test pytest --cov=src --cov-fail-under=97
$ uv build
$ cd docs && uv run --group docs make html
```

These are the same commands run by the `Workflow Push` GitHub Action
(`.github/workflows/wf-push.yml`) on every push, so running them locally before opening a
PR will catch most CI failures early.

:::{note}
Looking for the `tox`-based workflow described in older versions of this guide? The
project migrated its own build/test/lint/doc tooling to `uv`. `tox` is still used by
*generated* downstream projects created via `nasdaq-protocols-create-new-project` --
see {ref}`user-guide-create-new-project` -- that is unrelated to building this repository.
:::

## FAQ

- **Why is pycharm debugger not stopping at breakpoints?**
  Disable the coverage statement from pytest.ini. Refer <https://stackoverflow.com/a/56235965/4248850>

- **Why is the coverage not reported in pycharm?**
  Disable the coverage statement from pytest.ini
