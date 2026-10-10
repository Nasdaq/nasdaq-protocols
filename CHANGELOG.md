# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project uses tagged releases published to [PyPI](https://pypi.org/project/nasdaq-protocols/).

## [Unreleased]

No changes yet.

## [1.3.0] - 2026-10-10

- FIX: session-level sequence gap detection and recovery on login (#73)
- Fix: `Record.as_collection` now prints nested `Record`s correctly (#72)
- Build: migrated the project's own build/test/lint/doc tooling from `tox` to
  [`uv`](https://docs.astral.sh/uv/) (#69)
- Perf: optional `performance` extra installing `uvloop` for ~4-5x faster event loop
  scheduling, activated via `nasdaq_protocols.common.use_fast_loop()` (#70)
- Docs: migrated `docs/*.rst` to Markdown (MyST), added root `LICENSE`, `CONTRIBUTING.md`,
  this changelog, and rewrote `README.md` (addresses #46, #47)

## [1.2.4] - 2026-01-15

Released together with the `1.2.0`-`1.2.4` series below (iterative CI/build fixes landed
over a single week):

- Build: explicit build steps for build and doc jobs (#67, #68)
- CI: build documentation when pushing to `gh-pages` and `main` (#66)
- CI: publish to GitHub Pages only on push to `main` (#65)
- CI: add jobs to publish the package to PyPI and TestPyPI (#64)
- Feature: graceful shutdown for sessions (#63)
- Docs: fixed docstrings for OUCH and SQF decode methods (#62)

## [1.1.4] / [1.1.3] - 2025-09-19

- Feature: configurable length types for array fields (#61)
- Feature: `nasdaq-sqf-codegen` CLI for SQF code generation (#60)

## [1.1.2] - 2025-08-22

- Feature: generic `tail` command for all SOUP-based applications (#59)

## [1.1.1] - 2025-04-04

- Fix: pytest configuration fixes (#51)

## [1.1.0] - 2025-04-02

- Feature: ASN.1-over-SOUP application support, `asn1soup` codegen CLI (#48, #49)

## [1.0.1] - 2025-01-24

- Fix: `fix-datasegment.field` now returns the result in the correct units (#39)
- Fix: resolved issue #37

## [1.0.0] - 2025-01-22

First stable release. Includes SOUP, OUCH, ITCH, SQF and FIX session/message support, the
`nasdaq-protocols-create-new-project` scaffolding CLI, and Sphinx documentation published to
GitHub Pages.

## [0.0.1a1] - [0.0.1.a6] - 2024-09-03 to 2025-01-22

Initial alpha releases: SOUP transport layer, OUCH/ITCH/SQF protocol support, FIX parser and
session handling, documentation infrastructure, and CI setup.

[Unreleased]: https://github.com/Nasdaq/nasdaq-protocols/compare/1.3.0...main
[1.3.0]: https://github.com/Nasdaq/nasdaq-protocols/releases/tag/1.3.0
[1.2.4]: https://github.com/Nasdaq/nasdaq-protocols/releases/tag/1.2.4
[1.1.4]: https://github.com/Nasdaq/nasdaq-protocols/releases/tag/1.1.4
[1.1.3]: https://github.com/Nasdaq/nasdaq-protocols/releases/tag/1.1.3
[1.1.2]: https://github.com/Nasdaq/nasdaq-protocols/releases/tag/1.1.2
[1.1.1]: https://github.com/Nasdaq/nasdaq-protocols/releases/tag/1.1.1
[1.1.0]: https://github.com/Nasdaq/nasdaq-protocols/releases/tag/1.1.0
[1.0.1]: https://github.com/Nasdaq/nasdaq-protocols/releases/tag/1.0.1
[1.0.0]: https://github.com/Nasdaq/nasdaq-protocols/releases/tag/1.0.0
