# PyConflict roadmap

## Current release status

Version 2.0.0 was published to PyPI on 2026-11-23. The current
CLI checks direct package dependencies, evaluates PEP 508 markers, audits installed
requirements, checks batches of package candidates, and filters stable versions by
Python compatibility. The repository also contains Cursor guidance, an MCP server,
a VS Code extension source package, and an opt-in Redis team baseline.

## Current limits

- `check-add` checks direct dependencies only. It does not resolve transitive dependency graphs.
- Optional extras are not included in `check-add`.
- `batch-check` accepts package names and exact `==` pins; it rejects ranges, extras, and markers.
- Private package indexes are not supported.
- The MCP server passed a real stdio handshake and tool-discovery check; this check now runs in CI.
- The Redis adapter passed a real-service round trip, TTL, workspace-isolation, and clear check;
  CI starts a Redis service for the same acceptance test.
- The VS Code extension was installed in an isolated profile and activated in an Extension
  Development Host against a clean workspace containing `requirements.txt`.
- The Cursor rules were copied into a clean sample project and its PyConflict CLI command was
  verified. Cursor IDE rule loading could not be checked because this host has no Cursor IDE.
- Accuracy has not been measured. PyConflict does not publish a confidence score.

## Next work

### 1. Complete integration acceptance

- [x] Add an MCP stdio client/server test to CI and verify local startup and tool discovery.
- [x] Exercise the Redis adapter against a disposable Redis service locally and in CI.
- [x] Install and activate the VS Code extension in an Extension Development Host.
- [x] Follow the Cursor setup steps in a clean sample project; verify Cursor IDE rule loading on a
  host with Cursor installed.

### 2. Resolve transitive dependencies

Implement a bounded dependency graph walk before restoring any `--deep` option. The
implementation should define marker evaluation, cycle handling, version constraints,
depth or node limits, and useful `required_by` paths. It must not install or modify
packages. Add deterministic fixtures for conflicts, compatible paths, cycles, and
incomplete metadata.

### 3. Add optional extras support

Parse requested extras and include only requirements guarded by those extras and the
current environment. Keep the default check limited to the base package. Add tests for
multiple extras, markers, and unknown extras before documenting support.

### 4. Consider private indexes

Design index configuration and credential handling before implementation. Never put
credentials in command output, cache keys, logs, or checked-in configuration examples.

## Release gate

For future releases, update the changelog, verify the package metadata and
wheel, run the full CI suite, test the documented installation flow, and confirm the
release version is available from the intended package index. A merge or successful
CI run alone does not indicate publication. The core build uses setuptools `<77`
because Python 3.8-compatible setuptools rejects the SPDX string form introduced in
version 77. This bounds the backend to a version that accepts the current MIT license
metadata without emitting the new deprecation warning. The MCP package uses SPDX
metadata and setuptools 77+ because it requires Python 3.11+. Python 3.8 execution
was confirmed in CI. The tag-triggered OIDC publishing job passed for `v2.0.0`; PyPI
reports the release and a clean virtual environment installed it from the index.

## Historical planning

The earlier ten-version strategy is preserved in [ROADMAP-ARCHIVE.md](ROADMAP-ARCHIVE.md).
Its estimates and feature claims are proposals, not current project status.
