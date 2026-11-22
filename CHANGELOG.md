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
- 45 unit tests, 7 offline MCP tests, and 42 PyPI integration tests passed locally.
- Black, Ruff, and mypy passed.
- The VS Code extension type check and VSIX packaging passed; npm audit found no vulnerabilities.
- Core and MCP wheels built locally. No package release was made.
