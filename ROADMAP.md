# PyConflict roadmap

## Current release status

Version 2.0.0 is implemented in the repository and remains unreleased. The current
CLI checks direct package dependencies, evaluates PEP 508 markers, audits installed
requirements, checks batches of package candidates, and filters stable versions by
Python compatibility. The repository also contains Cursor guidance, an MCP server,
a VS Code extension source package, and an opt-in Redis team baseline.

## Current limits

- `check-add` checks direct dependencies only. It does not resolve transitive dependency graphs.
- Optional extras are not included in `check-add`.
- `batch-check` accepts package names and exact `==` pins; it rejects ranges, extras, and markers.
- Private package indexes are not supported.
- Integrations have build and unit coverage, but host-level acceptance is still needed for Cursor,
  VS Code, MCP stdio startup, and a real Redis service.
- Accuracy has not been measured. PyConflict does not publish a confidence score.

## Next work

### 1. Complete integration acceptance

- Add an MCP stdio client/server test to CI.
- Exercise the Redis adapter against a disposable Redis service.
- Install and activate the VS Code extension in an Extension Development Host.
- Follow the Cursor setup guide in a clean sample project.

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

Before publishing a version, update the changelog, verify the package metadata and
wheel, run the full CI suite, test the documented installation flow, and confirm the
release version is available from the intended package index. A merge or successful
CI run alone does not indicate publication. Resolve the current setuptools license
metadata deprecation warnings while preserving the Python 3.8 build matrix.

## Historical planning

The earlier ten-version strategy is preserved in [ROADMAP-ARCHIVE.md](ROADMAP-ARCHIVE.md).
Its estimates and feature claims are proposals, not current project status.
