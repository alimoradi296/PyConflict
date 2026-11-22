# PyConflict

[![PyPI version](https://badge.fury.io/py/pyconflict.svg)](https://badge.fury.io/py/pyconflict)
[![Python versions](https://img.shields.io/pypi/pyversions/pyconflict.svg)](https://pypi.org/project/pyconflict/)
[![CI](https://github.com/alimoradi296/PyConflict/workflows/CI/badge.svg)](https://github.com/alimoradi296/PyConflict/actions)
[![codecov](https://codecov.io/gh/alimoradi296/PyConflict/branch/main/graph/badge.svg)](https://codecov.io/gh/alimoradi296/PyConflict)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Python Dependency Conflict Checker - Check before you install**

PyConflict answers one critical question: **"Will adding this package break my environment?"**

Unlike existing tools that detect conflicts *after* installation, PyConflict is **proactive** - it checks dependencies before making changes.

## Why PyConflict?

**The Problem:**
```bash
$ pip install django==3.2
# ... 5 minutes later ...
ERROR: django 3.2 requires asgiref>=3.3.2,<4
but channels 4.0 requires asgiref>=3.5.0
```

**The Solution:**
```bash
$ pyconflict check-add django==3.2
✗ Cannot add django==3.2

  Conflicts detected:
    • asgiref
      Required: >=3.3.2,<4
      Installed: 3.7.2

  Suggestions:
    → Upgrade django to 4.2+ (compatible with channels 4.0)
```

## Features

- ✅ **Proactive conflict detection** - Check dependency constraints before installing
- ✅ **AI-assistant friendly** - JSON output for Claude Code, Cursor, Copilot
- ✅ **Cached PyPI metadata** - Reuse package data between checks
- ✅ **Direct dependencies** - Checks package's immediate dependencies against installed versions
- ✅ **Latest stable version** - Find the newest non-prerelease version
- ✅ **Clean Architecture** - Maintainable, testable, extensible codebase
- ✅ **Tests** - Unit and integration test suites are included

### Planned
- **Next**: Extras handling and MCP server for Claude Code
- **Phase 3** (Month 2): Transitive dependency checking, Python API, CI/CD templates
- **Phase 4** (Months 3-4): Private PyPI support, enterprise features

## Installation

### From PyPI (Recommended)

```bash
pip install pyconflict
```

### From Source

```bash
git clone https://github.com/alimoradi296/PyConflict.git
cd PyConflict
pip install -e ".[dev]"
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

## Usage

### Command: `check-add`

Check if adding a package will cause conflicts with your current environment.

```bash
pyconflict check-add <package> [OPTIONS]
```

**Options:**
- `--version TEXT` - Specific version to check
- `--json` - Output in JSON format
- `--deep` - Check transitive dependencies (Phase 3)

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
  Confidence: 90%

The confidence value is a heuristic score, not a measured accuracy rate.

# Conflict detected
$ pyconflict check-add django==3.2
✗ Cannot add django==3.2

Conflicts detected:
  • asgiref
    Required: >=3.3.2,<4
    Installed: 3.7.2

Suggestions:
  → Upgrade django to 4.2+ (compatible with channels 4.0)

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
      "required": ">=3.3.2,<4",
      "installed": "3.7.2",
      "required_by": "django==3.2.0",
      "severity": "error"
    }
  ],
  "suggestions": [
    "Upgrade django to 4.2+ (compatible with channels 4.0)"
  ],
  "confidence": 0.9,
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

- ⚠️ **Direct dependencies only** - Transitive deps not checked (Phase 3: --deep flag)
- ⚠️ **Extras not checked** - `package[security]` extras are not included
- ⚠️ **Public PyPI only** - Private registries not supported (Phase 4)
- ⚠️ **Suggestions only** - No automatic fixes (by design - user decides)

**Accuracy is not measured.** The tool checks direct dependency constraints against
the current environment. It does not resolve the full dependency graph.

See [Roadmap](ROADMAP.md) for planned enhancements.

## Roadmap

### Current implementation
- ✅ Direct dependency conflict detection
- ✅ PEP 508 environment marker evaluation
- ✅ Installed environment check
- ✅ Batch package checks
- ✅ Latest stable version lookup
- ✅ CLI with JSON output

### Planned
- Extras handling (`package[extra]`)
- MCP server for Claude Code
- Enhanced error messages

### 🚀 v3.0 - Deep Analysis (Month 2)
- Transitive dependency checking (--deep flag)
- Python API for programmatic use
- Configuration file support (.pyconflict.yml)
- CI/CD integration templates

### 🚀 v4.0+ - Enterprise & Beyond
- Private PyPI repository support
- Team collaboration features
- Security scanning integration
- Multi-language support (npm, cargo, etc.)

See [ROADMAP.md](ROADMAP.md) for the longer-term project direction.

## FAQ

**Q: How is this different from `pip check`?**
A: `pip check` is reactive - it checks for conflicts after installation. PyConflict is proactive - it checks before you install.

**Q: Does it work with private PyPI repositories?**
A: Not in MVP. Phase 2 will add support for private registries.

**Q: Can it automatically fix conflicts?**
A: No. PyConflict provides suggestions, but you decide what to do. Automatic fixes are too risky.

**Q: How accurate is it?**
A: No accuracy percentage has been measured. The current check covers direct dependencies and has documented limitations around transitive dependencies, markers, and extras.

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

- 🐛 **Report bugs**: [GitHub Issues](https://github.com/alimoradi296/PyConflict/issues)
- 💡 **Request features**: [GitHub Discussions](https://github.com/alimoradi296/PyConflict/discussions)
- 💬 **Ask questions**: [GitHub Discussions](https://github.com/alimoradi296/PyConflict/discussions)
- 🤝 **Contribute**: See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- **GitHub**: https://github.com/alimoradi296/PyConflict
- **PyPI**: https://pypi.org/project/pyconflict/
- **Documentation**: https://pyconflict.readthedocs.io
- **Issues**: https://github.com/alimoradi296/PyConflict/issues
- **Discussions**: https://github.com/alimoradi296/PyConflict/discussions
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
