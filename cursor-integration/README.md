# PyConflict Integration for Cursor

Make Cursor AI-safe for Python dependency management.

## Overview

This integration enables Cursor to automatically check Python dependencies before adding them, preventing conflicts and broken environments.

## Installation

### Step 1: Install PyConflict

```bash
pip install "pyconflict>=2.0.0"
```

### Step 2: Copy Rules to Your Project

Copy the `.cursor/rules` file to your project's root directory:

```bash
cp cursor-integration/.cursor/rules /path/to/your/project/.cursor/rules
```

Or create the file manually in your project:

```bash
mkdir -p .cursor
# Copy the content from cursor-integration/.cursor/rules
```

### Step 3: Restart Cursor

Close and reopen Cursor to load the new rules.

## Verification

Test that Cursor uses PyConflict:

**User:** "Add django to my project"

**Expected Cursor Behavior:**
1. Runs `pyconflict check-add django --json`
2. Analyzes the result
3. Only adds if safe
4. Shows conflicts if any

## How It Works

Cursor reads the `.cursor/rules` file and follows these rules when you ask to add Python packages:

```
User: "Add package X"
  ↓
Cursor: Run `pyconflict check-add X --json`
  ↓
Safe? → Add to requirements.txt
Conflict? → Show conflicts + suggestions
```

## Features

### Automatic Safety Checks

Cursor will automatically run PyConflict before:
- Adding a single package
- Adding multiple packages
- Upgrading a package
- Changing versions

### Intelligent Suggestions

When conflicts are detected, Cursor will:
- Show what conflicts were found
- Display PyConflict's suggestions
- Offer alternative versions

### Batch Operations

When adding multiple packages, Cursor uses batch checking for efficiency:

```
User: "Add django, celery, redis"
Cursor: [Checks all three at once via batch-check]
```

## Usage Examples

### Example 1: Safe Package

**User:** "Add requests to my project"

**Cursor:**
```bash
# Checking if requests is safe to add...
pyconflict check-add requests --json

# Result: Safe ✓
# Adding requests==2.31.0 to requirements.txt
```

**Output:**
```
✓ Added requests==2.31.0 to requirements.txt
```

### Example 2: Conflict Detected

**User:** "Add django==3.2"

**Cursor:**
```bash
# Checking if django==3.2 is safe to add...
pyconflict check-add django --version 3.2 --json

# Result: Conflict detected ✗
```

**Output:**
```
✗ Cannot add django==3.2 - conflicts detected:

Conflicts:
  • asgiref
    Required: >=3.3.2,<4
    Installed: 3.7.2
    Required by: django==3.2

Suggestions:
  → Upgrade django to 4.2+ (compatible with your current packages)

Would you like me to try django==4.2 instead?
```

### Example 3: Multiple Packages

**User:** "Add fastapi, uvicorn, and pydantic to my project"

**Cursor:**
```bash
# Checking 3 packages...
# Creating batch file...
pyconflict batch-check --file /tmp/packages.txt --json

# Results:
# ✓ fastapi - Safe
# ✓ uvicorn - Safe
# ✓ pydantic - Safe
```

**Output:**
```
✓ All 3 packages are safe to add!

Added to requirements.txt:
  fastapi==0.104.1
  uvicorn==0.24.0
  pydantic==2.5.0
```

### Example 4: Version Upgrade

**User:** "Upgrade django to the latest version"

**Cursor:**
```bash
# Getting latest stable version...
pyconflict stable django --json
# Latest: 5.0.1

# Checking if upgrade is safe...
pyconflict check-add django --version 5.0.1 --json
# Result: Safe ✓
```

**Output:**
```
✓ Safe to upgrade to django==5.0.1
Updated requirements.txt: django==4.2 → django==5.0.1
```

## Configuration

### Custom Rules

You can customize the `.cursor/rules` file to match your workflow:

```
# Example: Always check environment after changes
After adding packages, always run:
  pyconflict check-env --json
```

### Team Workspace

Team baseline checks require the optional Redis support and are not enabled by these Cursor rules. See the root README for the explicit `team-check` commands.

## Troubleshooting

### Issue: Cursor doesn't follow rules

**Solution 1:** Make sure `.cursor/rules` is in your project root
```bash
ls -la .cursor/rules
```

**Solution 2:** Restart Cursor
```bash
# Close and reopen Cursor
```

**Solution 3:** Check PyConflict is installed
```bash
pyconflict --version
# Should show: pyconflict, version 2.0.0 or higher
```

### Issue: Rules file not found

**Solution:** Create the directory and file
```bash
mkdir -p .cursor
cp /path/to/cursor-integration/.cursor/rules .cursor/rules
```

### Issue: PyConflict commands fail

**Solution:** Verify PyConflict works
```bash
pyconflict check-add requests --json
# Should return JSON output
```

### Issue: Slow performance

**Solution:** PyConflict caches package metadata locally. Network requests and cache state can affect response time.

## Advanced Usage

### Pre-commit Hook Integration

Combine with pre-commit hooks:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pyconflict-check
        name: Check dependencies
        entry: pyconflict check-env
        language: system
        pass_filenames: false
```

### CI/CD Integration

Add to GitHub Actions:

```yaml
# .github/workflows/dependencies.yml
- name: Check dependencies
  run: |
    pip install pyconflict
    pyconflict check-env --json
```

### Custom Scripts

Create custom scripts that Cursor can use:

```bash
#!/bin/bash
# scripts/safe-add.sh

PACKAGE=$1

if pyconflict check-add "$PACKAGE" --json > /tmp/result.json; then
    VERSION=$(jq -r '.package.version' /tmp/result.json)
    echo "$PACKAGE==$VERSION" >> requirements.txt
    echo "✓ Added $PACKAGE==$VERSION"
else
    echo "✗ Cannot add $PACKAGE - conflicts detected"
    jq '.conflicts' /tmp/result.json
    exit 1
fi
```

Then in Cursor:
```
User: "Add fastapi"
Cursor: ./scripts/safe-add.sh fastapi
```

## Best Practices

1. **Always use latest PyConflict**
   ```bash
   pip install --upgrade pyconflict
   ```

2. **Review conflicts before overriding**
   - Treat the confidence value as a heuristic, not a measured accuracy probability.
   - Review caveats and resolve uncertain results before changing dependencies.

3. **Use batch checks for multiple packages**
   - More efficient than one-by-one
   - Better user experience

4. **Keep rules file in version control**
   ```bash
   git add .cursor/rules
   git commit -m "Add PyConflict rules for Cursor"
   ```

5. **Share with team**
   - Everyone gets safe dependency management
   - Consistent behavior across team

## Examples in Action

See [example-usage.md](example-usage.md) for real-world scenarios.

## Links

- **PyConflict**: https://github.com/alimoradi296/PyConflict
- **Cursor**: https://cursor.sh
- **Documentation**: https://pyconflict.readthedocs.io
- **Issues**: https://github.com/alimoradi296/PyConflict/issues

## Support

- **Questions**: Open a discussion on GitHub
- **Bugs**: Report an issue
- **Feature requests**: Open a discussion

---

**Make Cursor safe for Python dependencies!**
