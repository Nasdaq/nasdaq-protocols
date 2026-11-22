# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project uses tagged releases published to [PyPI](https://pypi.org/project/nasdaq-protocols/).

## [Unreleased]

- Fix: session robustness and usability fixes
  - the reader is now event driven instead of polling every 0.1ms, which removes idle CPU
    usage and speeds up bursts; malformed data and handler errors are logged with a
    traceback and close the session instead of silently killing the reader
  - closing a session no longer drops or cancels queued messages: on a server initiated
    close, OUCH/ITCH/SQF/ASN1 sessions deliver every message received before the close,
    and a graceful close no longer hangs when no dispatcher is draining the queue
  - OUCH/ITCH/SQF/ASN1 `close()` now sends a SOUP `LogoutRequest` before disconnecting
  - FIX: messages arriving in the same packet as the Logon reply are now sequence checked
    instead of bypassing gap detection
  - FIX: an int `sequence` no longer breaks `send_msg`; `connect_async` accepts an
    optional `connect_timeout`
  - sync SOUP `send_unseq_data` now runs on the session's event loop thread
  - `set_handlers` no longer replaces the close handler when it raises
  - falsy messages are no longer treated as an empty queue
- Feature: `async with` / `with` support for all sessions, `receive_msg` / `send_msg`
  aliases on the OUCH/ITCH/SQF/ASN1 and sync SOUP sessions, `session_id` defaults to `''`
  in `connect_async`
- Breaking: misspelled ASN1 names renamed, the old names are removed:
  `Ans1SoupSessionId` -> `Asn1SoupSessionId`, `OnAns1CloseCoro` -> `OnAsn1CloseCoro`,
  `Ans1Generator` -> `Asn1Generator`, template `ans1_soup_app.mustache` ->
  `asn1_soup_app.mustache`
- Refactor: `Asn1SoupClientSession` now builds on `SoupAppClientSession` instead of
  duplicating it; internal session state is no longer a constructor argument
- Chore: bump `certifi` from 2026.6.17 to 2026.10.19 (#86)
- Chore: bump `pylint` from 4.0.6 to 4.0.9 (#87)
- Chore: bump `urllib3` from 2.7.0 to 2.8.0 (#79)
- CI: added CodeQL security scanning, Codecov coverage reporting/badge, and
  enabled Dependabot security updates.

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
