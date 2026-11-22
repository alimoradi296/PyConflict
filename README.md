# PyConflict

[![CI](https://github.com/alimoradi296/PyConflict/workflows/CI/badge.svg)](https://github.com/alimoradi296/PyConflict/actions)
[![PyPI version](https://img.shields.io/pypi/v/pyconflict.svg)](https://pypi.org/project/pyconflict/)
[![codecov](https://codecov.io/gh/alimoradi296/PyConflict/branch/main/graph/badge.svg)](https://codecov.io/gh/alimoradi296/PyConflict)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Python Dependency Conflict Checker - Check before you install**

PyConflict checks Python package dependency constraints before installation. It supports
PEP 508 environment markers, installed-environment audits, batch checks, and integrations
for AI coding tools.

It answers one question: **"Will adding this package conflict with versions already installed?"**

Unlike existing tools that detect conflicts *after* installation, PyConflict is **proactive** - it checks dependencies before making changes.

## Why PyConflict?

**The Problem:**
```bash
# requirements.txt pins django==3.2 and asgiref==3.2.0
$ python -m pip install -r requirements.txt
ERROR: django==3.2 requires asgiref>=3.3.2,<4, but asgiref==3.2.0 is pinned
```

**The Solution:**
```bash
$ pyconflict check-add django==3.2
✗ Cannot add django==3.2

  Conflicts detected:
    • asgiref
      Required: <4,>=3.3.2
      Installed: 3.2.0

  Suggestions:
    → Upgrade 'asgiref' from 3.2.0 to satisfy django's requirement (<4,>=3.3.2)
```

## Features

- ✅ **Proactive conflict detection** - Check dependency constraints before installing
- ✅ **AI-assistant friendly** - JSON output for Claude Code, Cursor, Copilot
- ✅ **Editor integrations** - Cursor instructions, an MCP server, and a VS Code extension
- ✅ **PEP 508 markers** - Ignore requirements that do not apply to the selected Python and platform
- ✅ **Cached PyPI metadata** - Reuse package data between checks
- ✅ **Direct dependencies** - Checks package's immediate dependencies against installed versions
- ✅ **Latest stable version** - Find the newest non-prerelease version
- ✅ **Clean Architecture** - Maintainable, testable, extensible codebase
- ✅ **Tests** - Unit and integration test suites are included

### Current limits
- `check-add` checks direct dependencies. It does not resolve transitive dependencies.
- Optional extras such as `package[security]` are not included.
- `batch-check` accepts package names and exact `==` pins only.
- Private package indexes are not supported.

## Installation

### From PyPI

```bash
python -m pip install pyconflict
```

### Development install

```bash
python -m pip install -e ".[dev]"
```

### Verify Installation

```bash
pyconflict --help
```

## Quick Start

### Check if a package is safe to add

```bash
# Check latest version
$ pyconflict check-add tensorflow

# Check specific version
$ pyconflict check-add django==3.2

# JSON output (for AI tools)
$ pyconflict check-add requests --json
```

### Get latest stable version

```bash
# Latest version
$ pyconflict stable pandas

# Filter by Python version
$ pyconflict stable numpy --python-version 3.8
```

### Check the installed environment and multiple package candidates

```bash
pyconflict check-env --json
pyconflict batch-check -p django -p "requests==2.31.0" --json
```

`batch-check` accepts package names or exact `==` pins. It rejects version ranges,
extras, and environment markers.

### Optional team baseline check

From the repository checkout, install Redis support with
`python -m pip install ".[team]"`, then configure
`PYCONFLICT_WORKSPACE_ID` and `PYCONFLICT_REDIS_URL`. Compare the current
environment with a saved baseline by running `pyconflict team-check`. To
explicitly save the current package names and versions as the shared baseline,
run `pyconflict team-check --set-standard`. Saving sends those names and
versions to the configured Redis service; a normal check only reads the
baseline.

## Usage

### Command: `check-add`

Check if adding a package will cause conflicts with your current environment.

```bash
pyconflict check-add <package> [OPTIONS]
```

**Options:**
- `--version TEXT` - Specific version to check
- `--json` - Output in JSON format

**Exit codes:**
- `0` - Safe to add, no conflicts
- `1` - Conflict detected
- `2` - Package not found
- `4` - Repository error
- `5` - Unexpected error

**Examples:**

```bash
# Safe to add
$ pyconflict check-add fastapi
✓ Safe to add fastapi==0.104.1

# Conflict detected
$ pyconflict check-add django==3.2
✗ Cannot add django==3.2

Conflicts detected:
  • asgiref
    Required: <4,>=3.3.2
    Installed: 3.2.0

Suggestions:
  → Upgrade 'asgiref' from 3.2.0 to satisfy django's requirement (<4,>=3.3.2)

# JSON output
$ pyconflict check-add django==3.2 --json
{
  "status": "conflict",
  "exit_code": 1,
  "package": {
    "name": "django",
    "version": "3.2.0"
  },
  "conflicts": [
    {
      "dependency": "asgiref",
      "required": "<4,>=3.3.2",
      "installed": "3.2.0",
      "required_by": "django==3.2.0",
      "severity": "error"
    }
  ],
  "suggestions": [
    "Upgrade 'asgiref' from 3.2.0 to satisfy django's requirement (<4,>=3.3.2)"
  ],
  "caveats": [
    "Only direct dependencies checked (not transitive)",
    "Optional extras not included"
  ]
}
```

### Command: `stable`

Get the latest stable (non-prerelease) version of a package.

```bash
pyconflict stable <package> [OPTIONS]
```

**Options:**
- `--python-version TEXT` - Filter by Python version compatibility
- `--json` - Output in JSON format

**Examples:**

```bash
$ pyconflict stable pandas
pandas==2.1.4

$ pyconflict stable numpy --python-version 3.8
numpy==1.24.4 (filtered by Python version)
```

## AI Assistant Integration

### For Claude Code

PyConflict is designed to be called by AI coding assistants:

```bash
# Claude internally runs:
result=$(pyconflict check-add tensorflow --json)
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "tensorflow==2.15.0" >> requirements.txt
else
    # Show conflict to user
    echo "Cannot add tensorflow: conflicts detected"
fi
```

### For Cursor

Add to `.cursor/rules`:
```
Before adding Python packages:
1. Run: pyconflict check-add <package> --json
2. Only proceed if exit_code == 0
```

## Architecture

PyConflict follows **Clean Architecture** principles:

```
┌─────────────────────┐
│   CLI (Typer)       │  ← Presentation Layer
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   Use Cases         │  ← Application Layer
│ • CheckAddPackage   │
│ • GetLatestStable   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Domain Services    │  ← Domain Layer
│ • ConflictDetector  │
│ • VersionResolver   │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Infrastructure     │  ← Infrastructure Layer
│ • PyPI Repository   │
│ • Disk Cache        │
│ • Pip Environment   │
└─────────────────────┘
```

**Key benefits:**
- **Testable**: Domain logic has zero external dependencies
- **Swappable**: Can replace PyPI with private registry without touching business logic
- **Maintainable**: Clear boundaries prevent spaghetti code

## Performance

PyConflict is designed for speed:

- **Cached requests**: < 2 seconds
- **Uncached requests**: < 10 seconds
- **Stable version lookup**: < 5 seconds
- **Parallel requests**: Supports concurrent package checks

The timings above are targets and have not been verified for this checkout.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/alimoradi296/PyConflict.git
cd PyConflict

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pyconflict --cov-report=html

# Run only unit tests (fast)
pytest tests/unit -v

# Run integration tests (requires network)
pytest tests/integration -v -m integration

# Run specific test
pytest tests/unit/domain/test_version_resolver.py
```

### Code Quality

```bash
# Format code
black src tests

# Lint
ruff check src tests

# Type check
mypy src

# Run all checks (CI simulation)
black --check src tests && ruff check src tests && mypy src && pytest
```

## Limitations

PyConflict checks direct dependencies for `check-add` and installed distribution
requirements for `check-env`:

- ⚠️ **Direct dependencies only** - Transitive dependencies are not checked
- ⚠️ **Extras not checked** - `package[security]` extras are not included
- ⚠️ **Public PyPI only** - Private registries are not supported
- ⚠️ **Suggestions only** - No automatic fixes (by design - user decides)

**Accuracy is not measured.** The tool checks direct dependency constraints against
the current environment. It does not resolve the full dependency graph.

PyConflict does not report a confidence percentage. Its checks cover documented inputs;
they are not a guarantee that an installation will succeed.

See [Roadmap](ROADMAP.md) for current priorities.

## Roadmap

### Current implementation
- ✅ Direct dependency conflict detection
- ✅ PEP 508 environment marker evaluation
- ✅ Installed environment check
- ✅ Batch package checks
- ✅ Latest stable version lookup
- ✅ CLI with JSON output
- ✅ Redis-backed team baseline (explicit opt-in when saving)
- ✅ MCP server and VS Code extension source package
- ✅ Cursor setup instructions

### Planned
- Transitive dependency analysis with explicit graph and cycle handling
- Extras handling (`package[extra]`)
- Real-service acceptance checks for MCP stdio, Redis, and the VS Code host
- Private index support after credential and configuration behavior is designed

See [ROADMAP.md](ROADMAP.md) for current project priorities.

## FAQ

**Q: How is this different from `pip check`?**
A: `pip check` is reactive - it checks for conflicts after installation. PyConflict is proactive - it checks before you install.

**Q: Does it work with private PyPI repositories?**
A: No. PyConflict currently reads package metadata from public PyPI.

**Q: Can it automatically fix conflicts?**
A: No. PyConflict provides suggestions, but you decide what to do. Automatic fixes are too risky.

**Q: How accurate is it?**
A: We have not measured accuracy. `check-add` checks direct dependencies and evaluates their environment markers. It does not check transitive dependencies or optional extras.

**Q: Does it replace poetry/pip-tools?**
A: No. PyConflict is a checker, not a package manager or lock file tool. Use it alongside your existing tools.

## Contributing

Contributions are welcome! We need help with:

- 🐛 Bug reports and fixes
- ✨ Feature implementations
- 📝 Documentation improvements
- 🧪 Test coverage expansion
- 🌍 Translations (future)

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork and clone the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure all tests pass (`pytest`)
5. Ensure code quality (`black`, `ruff`, `mypy`)
6. Commit with conventional commits (`feat:`, `fix:`, etc.)
7. Push and create a Pull Request

## Community

- 🐛 **Report bugs or request features**: [GitHub Issues](https://github.com/alimoradi296/PyConflict/issues)
- 💬 **Ask questions**: Open a GitHub issue and describe what you are trying to do.
- 🤝 **Contribute**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- **GitHub**: https://github.com/alimoradi296/PyConflict
- **Documentation**: [README](https://github.com/alimoradi296/PyConflict#readme)
- **Issues**: https://github.com/alimoradi296/PyConflict/issues
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

## Star History

If PyConflict saves you time, please give it a star on GitHub!

[![Star History Chart](https://api.star-history.com/svg?repos=alimoradi296/PyConflict&type=Date)](https://star-history.com/#alimoradi296/PyConflict&Date)

## Credits

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Packaging](https://packaging.pypa.io/) - Version parsing (PEP 440, PEP 508)

---

**Made with ❤️ for Python developers and AI coding assistants**
