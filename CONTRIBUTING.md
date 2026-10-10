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
  [CHANGELOG.md](CHANGELOG.md) under `[Unreleased]`. A CI check (`Changelog Check`) fails the
  PR if `CHANGELOG.md` isn't part of the diff.
  - If your change genuinely doesn't need a changelog entry (e.g. CI-only tweaks, typo
    fixes, internal refactors with no user-facing effect), apply the `skip-changelog`
    label to the PR to bypass the check:
    - GitHub UI: open the PR -> **Labels** (right sidebar) -> select `skip-changelog`.
    - CLI: `gh pr edit <PR_NUMBER> --add-label skip-changelog`
    Only maintainers/contributors with write access can add labels; if you can't add it
    yourself, ask a maintainer to apply it on your PR.
  - Dependabot PRs are handled automatically: a workflow (`Dependabot changelog entry`)
    adds a one-line `CHANGELOG.md` entry (derived from the PR title) to the PR branch when
    it's opened, so no label or manual edit is needed for dependency bumps.

## Documentation

Documentation source lives under `docs/` as Markdown (built with
[Sphinx](https://www.sphinx-doc.org/) + [MyST](https://myst-parser.readthedocs.io/)) and is
published automatically to [GitHub Pages](https://nasdaq.github.io/nasdaq-protocols/) on
every push to `main`. See the
[Developer's Guide](https://nasdaq.github.io/nasdaq-protocols/developer_guide.html) for more
detail.

## Cutting a release

Releases are fully automated (maintainers only):

1. Go to **Actions -> Release -> Run workflow**, enter the new version (e.g. `1.3.0`, no
   leading `v`), and run it.
2. The workflow rolls `CHANGELOG.md`'s `[Unreleased]` entries into a new dated
   `[<version>]` section, commits that change to `main`, then creates and pushes the
   `<version>` tag.
3. The tag push automatically triggers the build, then publishes to TestPyPI and PyPI.

No manual CHANGELOG editing or tagging is needed -- just make sure `[Unreleased]` has the
entries you want released before running the workflow.

## Reporting issues

Please use the [issue tracker](https://github.com/Nasdaq/nasdaq-protocols/issues) and
include a minimal reproduction where possible.
