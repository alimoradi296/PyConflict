# Contributing to PyConflict

Thank you for your interest in contributing to PyConflict! 🎉

We welcome contributions of all kinds: bug reports, feature requests, documentation improvements, and code contributions.

## Code of Conduct

Be respectful, inclusive, and constructive. We're here to build something useful together.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of Python packaging and dependencies

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/pyconflict.git
   cd pyconflict
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run tests to verify setup**
   ```bash
   pytest
   ```

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check existing issues to avoid duplicates.

**Good bug reports include:**
- Clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Python version and OS
- Relevant logs or error messages

**Example:**
```markdown
**Bug:** `pyconflict check-add` crashes on package with circular dependencies

**Steps to reproduce:**
1. Run `pyconflict check-add packageA`
2. See error traceback

**Expected:** Should handle circular deps gracefully
**Actual:** Crashes with RecursionError

**Environment:**
- Python 3.11.0
- PyConflict 0.1.0
- Ubuntu 22.04
```

### Suggesting Features

We love new ideas! Before suggesting a feature:

1. Check if it aligns with the project's MVP scope (see PRD.md)
2. Search existing feature requests
3. Clearly describe the use case and expected behavior

**Feature Request Template:**
```markdown
**Feature:** Add support for checking lock files (poetry.lock, Pipfile.lock)

**Use Case:** Many projects use poetry/pipenv instead of requirements.txt

**Proposed Solution:**
- Add `--lock-file` option
- Parse poetry.lock format
- Check against lock file dependencies

**Alternatives Considered:**
- Could integrate with poetry directly
- Could convert lock files to requirements.txt

**Phase:** Suggest for Phase 3 (not MVP)
```

### Contributing Code

#### Branch Naming

- `feature/your-feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/what-you-changed` - Documentation updates
- `test/what-you-tested` - Test additions

#### Development Workflow

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks**
   ```bash
   # Format code
   black src tests

   # Lint
   ruff check src tests

   # Type check
   mypy src

   # Run tests
   pytest
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add support for poetry.lock files"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `test:` - Test additions/changes
   - `refactor:` - Code refactoring
   - `perf:` - Performance improvements
   - `chore:` - Maintenance tasks

5. **Push and create a Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

#### Pull Request Guidelines

**Good PRs include:**
- Clear description of what changed and why
- Reference to related issues (e.g., "Fixes #123")
- Tests for new functionality
- Updated documentation
- All tests passing
- No merge conflicts

**PR Template:**
```markdown
## Description
Brief description of what this PR does

## Related Issues
Fixes #123

## Changes Made
- Added support for poetry.lock files
- Updated CLI to accept --lock-file option
- Added tests for lock file parsing

## Testing
- [ ] All existing tests pass
- [ ] Added new tests for new functionality
- [ ] Tested manually with poetry.lock file

## Checklist
- [ ] Code follows project style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No breaking changes (or documented if unavoidable)
```

## Code Style Guidelines

### Python Style

We follow PEP 8 with these tools:
- **Black** for formatting (line length: 100)
- **Ruff** for linting
- **MyPy** for type checking

### Architecture Guidelines

PyConflict follows **Clean Architecture**:

```
Domain Layer (innermost)
├── Zero external dependencies
├── Pure business logic
└── Fully unit testable

Application Layer
├── Use cases / workflows
└── Orchestrates domain services

Infrastructure Layer
├── PyPI client
├── Cache implementation
└── Environment reader

Presentation Layer (outermost)
├── CLI interface
└── Formatters
```

**Key principles:**
- **Dependencies point inward** - Domain never imports from infrastructure
- **Immutable entities** - Use `@dataclass(frozen=True)`
- **Repository pattern** - Infrastructure implements domain interfaces
- **No business logic in presentation** - CLI just calls use cases

### Testing Guidelines

We aim for **80%+ test coverage**.

**Test Structure:**
```
tests/
├── unit/
│   ├── domain/          # Pure unit tests (no mocks)
│   ├── application/     # Use case tests (mock repositories)
│   └── infrastructure/  # Integration tests (optional)
└── integration/         # Full integration tests (slow)
```

**Writing Good Tests:**

```python
def test_version_resolver_finds_compatible_version():
    """Test description in plain English."""
    # Given (setup)
    resolver = VersionResolver()
    versions = [Version("1.0.0"), Version("2.0.0")]
    constraint = SpecifierSet(">=1.5.0")

    # When (action)
    result = resolver.get_latest_compatible(versions, constraint)

    # Then (assertion)
    assert result == Version("2.0.0")
```

**Test Guidelines:**
- One assertion per test (when possible)
- Clear test names that describe behavior
- Use Given-When-Then structure
- No logic in tests (no loops, conditionals)
- Test edge cases and error conditions

### Documentation Guidelines

- Use docstrings for all public functions/classes
- Keep README.md up to date
- Add examples for new features
- Update CHANGELOG.md

**Docstring Format:**
```python
def check_compatibility(version: Version, constraint: SpecifierSet) -> bool:
    """Check if a version satisfies a constraint.

    Args:
        version: The version to check
        constraint: The constraint to check against

    Returns:
        True if version satisfies constraint, False otherwise

    Example:
        >>> check_compatibility(Version("2.0.0"), SpecifierSet(">=1.0"))
        True
    """
```

## Project Phases

PyConflict is developed in phases:

### Phase 1: MVP (Current) ✅
- Direct dependency checking
- CLI with JSON output
- Basic caching

### Phase 2: Enhanced (Coming Soon)
- Platform markers support
- Extras handling
- MCP server for Claude Code
- Better error messages

### Phase 3: Integration (Future)
- Transitive dependencies
- CI/CD examples
- Python API
- Configuration files

See **PRD.md** for full roadmap.

## Areas We Need Help With

### High Priority
- [ ] Platform marker support (PEP 508)
- [ ] Extras handling (`package[security]`)
- [ ] More comprehensive test coverage
- [ ] Performance optimization for large dependency trees

### Medium Priority
- [ ] MCP server implementation for Claude Code
- [ ] Support for poetry.lock and Pipfile.lock
- [ ] Better error messages with suggestions
- [ ] Cache warming for CI/CD

### Documentation
- [ ] Video tutorial
- [ ] Integration guides (GitHub Actions, pre-commit)
- [ ] More examples and use cases
- [ ] API documentation

### Future Features
- [ ] Web UI for conflict visualization
- [ ] Private PyPI repository support
- [ ] Dependency graph visualization
- [ ] Automatic conflict resolution (with confirmation)

## Questions?

- Open an issue for questions
- Tag maintainers if you need help: @alimoradi296
- Check existing issues and PRs for similar questions

## Recognition

All contributors will be recognized in:
- README.md contributors section
- Release notes
- Project website (when available)

Thank you for making PyConflict better! 🚀
