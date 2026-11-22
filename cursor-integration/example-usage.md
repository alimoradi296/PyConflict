# PyConflict command examples for Cursor

These examples describe commands currently provided by the CLI. PyConflict reports likely conflicts from available package metadata; it does not install packages or guarantee that an installation will succeed.

## Check one package

```bash
pyconflict check-add django --json
```

Use the process exit code and JSON `status`/`conflicts` fields. Show caveats to the user before proposing a dependency change.

## Check an exact version

```bash
pyconflict check-add django --version 5.0 --json
```

The version is only an example. Select the version requested by the user or returned by `pyconflict stable`; do not treat example versions as current recommendations.

## Check multiple packages

```bash
pyconflict batch-check -p django -p "requests==2.31.0" --json
```

`batch-check` accepts names and exact `==` pins. It returns one result per input with `safe`, `status`, and any conflicts. It rejects ranges, extras, and environment markers.

## Check the active environment

```bash
pyconflict check-env --json
```

This inspects installed distributions in the Python environment running PyConflict. It does not validate packages that are only listed in a manifest and not installed.

## Check the latest stable version

```bash
pyconflict stable pandas --python-version 3.11 --json
```

The optional Python version filters releases by their `Requires-Python` metadata.

## Team baseline

Team checks use the optional Redis extra and are not run automatically by Cursor rules. See the root README. Saving a baseline uploads the current package names and versions only when the operator runs `pyconflict team-check --set-standard`.
