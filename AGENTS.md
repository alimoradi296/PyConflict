# Repository guide for coding agents

## Project structure

- `src/pyconflict/domain/` contains entities, repository interfaces, and conflict rules.
- `src/pyconflict/application/use_cases/` contains application workflows.
- `src/pyconflict/infrastructure/` contains PyPI, cache, and installed-environment adapters.
- `src/pyconflict/presentation/cli/` contains Typer commands, dependency wiring, and output formatting.
- `tests/unit/` contains fast local tests. `tests/integration/` contains tests that contact PyPI.

Keep changes in the appropriate layer. In particular, keep CLI formatting and Typer types out of application and domain code.

## Local development

Install the project and development tools in an active virtual environment:

```bash
python -m pip install -e ".[dev]"
```

Run the checks used by the repository workflow:

```bash
pytest tests/unit
pytest tests/integration -m integration
black --check src tests
ruff check src tests
mypy src
```

Integration tests contact public PyPI and need network access. Run unit tests separately when network access is unavailable. Check that `python`, `pytest`, and other tools use the same virtual environment before interpreting environment-specific failures.

## Change workflow

- Add or update tests when behavior changes.
- Update `README.md` for user-visible command behavior. Keep release claims in `CHANGELOG.md` factual; the current version may still be unreleased.
- Run `git diff --check` and inspect the complete diff before committing.
- Stage specific files. Do not use `git add .`; this checkout may contain local notes, screenshots, or unfinished integrations.
- Use a `feature/`, `fix/`, `docs/`, or `test/` branch and a Conventional Commit message.
- Do not publish a release or claim a deployment from a branch push.
