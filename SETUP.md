# Setup Instructions

## Quick Start

### 1. Create and activate virtual environment

```bash
# Create venv
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### 2. Install in development mode

```bash
pip install -e ".[dev]"
```

### 3. Run tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pyconflict --cov-report=html

# Run specific tests
pytest tests/unit/domain/
pytest tests/unit/application/
```

### 4. Try the CLI

```bash
# Get help
pyconflict --help

# Check if a package is safe to add
pyconflict check-add requests

# Get latest stable version
pyconflict stable pandas

# JSON output (for AI tools)
pyconflict check-add django --json
```

## Development Workflow

### Code formatting

```bash
black src tests
```

### Linting

```bash
ruff check src tests
```

### Type checking

```bash
mypy src
```

### Run all quality checks

```bash
black src tests && ruff check src tests && mypy src && pytest
```

## Troubleshooting

### Issue: `pyconflict` command not found

**Solution**: Make sure you've installed in development mode and activated the venv:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

### Issue: Import errors

**Solution**: Install in editable mode from the project root:
```bash
pip install -e .
```

### Issue: Tests failing

**Solution**: Make sure all dev dependencies are installed:
```bash
pip install -e ".[dev]"
```

## Project Structure

```
pyconflict/
├── src/pyconflict/        # Source code
│   ├── domain/            # Business logic (pure Python)
│   ├── application/       # Use cases
│   ├── infrastructure/    # External service adapters
│   └── presentation/      # CLI interface
├── tests/                 # Test suite
│   └── unit/             # Unit tests
├── pyproject.toml        # Project configuration
└── README.md             # User documentation
```

## Next Steps

1. **Try the examples** in README.md
2. **Read the PRD** to understand the vision
3. **Check the architecture doc** for design details
4. **Write more tests** to expand coverage
5. **Add Phase 2 features** (platform markers, extras)
