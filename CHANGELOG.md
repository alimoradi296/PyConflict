# Changelog

This file records changes confirmed in the repository. It does not claim that a version was published.

## [2.0.0] - Unreleased

### Added
- `check-env` checks installed distribution requirements for missing or incompatible dependencies.
- `batch-check` checks package names and exact `==` pins, with a status and exit code for each result.
- PEP 508 environment markers are evaluated by `check-add` for the current Python version and platform.
- Stable-version lookup filters releases by `Requires-Python` when a Python version is supplied.
- `team-check` compares the installed package set with an explicitly configured Redis baseline. Saving a baseline is opt-in.
- Cursor and MCP integration instructions now match the current CLI. A VS Code extension source package is included with local VSIX build instructions.

### Changed
- The CLI version is read from package metadata.
- `check-add` no longer reports an uncalibrated confidence score.

### Fixed
- `check-env` no longer reports a clean environment without checking dependencies.
- `batch-check` rejects unsupported ranges, extras, and markers.
- The unsupported `check-add --deep` option and its misleading confidence adjustment were removed.
- Conflict suggestions now compare installed versions with parsed constraint bounds.
- Package and CLI versions are aligned at `2.0.0`.
- Optional dependency metadata uses the valid PEP 621 table structure.

### Verification
- 45 core unit tests and 8 MCP tests including a real stdio handshake passed locally; 42 PyPI integration tests and one live Redis service test also passed locally.
- The Redis adapter passed a live Redis service check for round trips, TTL, workspace isolation, and clearing.
- VS Code 2.0.0 was packaged, installed in an isolated profile, and activated in an Extension Development Host.
- The release wheel and its dependencies were installed in a clean sample project's virtual environment, and the Cursor rules and CLI command were checked there. Cursor IDE rule loading remains unverified because the IDE is not installed on the host.
- Black, Ruff, and mypy passed.
- The VS Code extension type check and VSIX packaging passed; npm audit found no vulnerabilities.
- Core wheel and source distribution, plus the MCP wheel, built locally. The core wheel installed and its metadata reports `Requires-Python: >=3.8` and `License: MIT`.
- The core build pins setuptools below 77 to avoid the PEP 639 warning on the supported Python 3.8 build path; the MCP package uses the SPDX form on its Python 3.11+ build path.
- Twine validation passed for the core wheel and source distribution.
- A tag-triggered GitHub Actions job is configured for PyPI Trusted Publishing; the pending publisher and release tag are not yet configured.
- No PyPI release was made.
