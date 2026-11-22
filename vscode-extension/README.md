# PyConflict VS Code Extension

Python dependency environment checks in Visual Studio Code.

## Features

- **Environment checks**: Check the installed environment with the selected Python interpreter
- **Status bar indicator**: See at a glance if your dependencies are safe
- **Command palette integration**: Check packages on demand
- **Hover tooltips**: See conflict details without leaving the editor
- **AI-friendly**: Works seamlessly with GitHub Copilot

## Installation

### From VSIX

```bash
code --install-extension pyconflict-vscode-2.0.0.vsix
```

## Prerequisites

PyConflict must be installed in your Python environment:

```bash
python -m pip install "git+https://github.com/alimoradi296/PyConflict.git"
```

The selected Python interpreter must be able to import `pyconflict`. The
Marketplace listing is not a verified release path yet; build and install a
local VSIX from this source tree.

## Usage

### Automatic Checking

When enabled, the extension checks the active Python environment when you open a Python workspace and after you save a dependency manifest. This checks installed distributions; it does not resolve uninstalled requirements from the manifest.

### Manual Checking

Use the Command Palette (Ctrl+Shift+P / Cmd+Shift+P):

- **PyConflict: Check Environment** - Check current environment for conflicts
- **PyConflict: Check Package** - Check if a specific package is safe to add
- **PyConflict: Get Latest Stable Version** - Get the latest stable version of a package

### Status Bar

The status bar shows your dependency health:

- ✓ No conflicts - All dependencies are compatible
- ⚠ 3 conflicts - Click to see details
- ✗ PyConflict error - Click to troubleshoot

## Configuration

Access settings via File > Preferences > Settings, then search for "PyConflict".

### Available Settings

- `pyconflict.enabled` (boolean, default: true)
  - Enable/disable the extension

- `pyconflict.autoCheck` (boolean, default: true)
  - Automatically check dependencies on file save

- `pyconflict.pythonPath` (string, default: "python")
  - Python executable used to run the installed PyConflict module (use "python", "python3", or a full path)

- `pyconflict.showStatusBar` (boolean, default: true)
  - Show conflict status in status bar

### Example Configuration

```json
{
  "pyconflict.enabled": true,
  "pyconflict.autoCheck": true,
  "pyconflict.pythonPath": "/usr/bin/python3",
  "pyconflict.showStatusBar": true
}
```

## Integration with GitHub Copilot

PyConflict works seamlessly with GitHub Copilot:

1. Copilot suggests adding a package
2. You add it to `requirements.txt`
3. PyConflict automatically checks for conflicts
4. Status bar shows if it's safe

**Example:**

```txt
# requirements.txt
django==3.2.0  # ⚠ Copilot suggested, but PyConflict warns about conflicts
```

## Troubleshooting

### Extension not working

1. Verify PyConflict is installed:
   ```bash
   pyconflict --version
   ```

2. Check Python path in settings:
   - Open VS Code settings
   - Search for "pyconflict.pythonPath"
   - Set to correct Python executable

3. Check output panel:
   - View > Output
   - Select "PyConflict" from dropdown

### Status bar not showing

1. Enable in settings: `pyconflict.showStatusBar: true`
2. Reload VS Code: Developer: Reload Window

### False positives

PyConflict v2.0 checks direct dependencies only. Some warnings may be platform-specific. See [Limitations](https://github.com/alimoradi296/PyConflict#limitations).

## Commands

All commands are available via Command Palette (Ctrl+Shift+P / Cmd+Shift+P):

| Command | Description |
|---------|-------------|
| `PyConflict: Check Environment` | Check current environment for conflicts |
| `PyConflict: Check Package` | Check if a specific package is safe to add |
| `PyConflict: Get Latest Stable Version` | Get the latest stable version of a package |

## Keyboard Shortcuts

No default keyboard shortcuts. You can add custom shortcuts:

1. File > Preferences > Keyboard Shortcuts
2. Search for "pyconflict"
3. Add your preferred shortcut

**Example:**
```json
{
  "key": "ctrl+shift+d",
  "command": "pyconflict.checkEnvironment"
}
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](https://github.com/alimoradi296/PyConflict/blob/main/CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- **PyConflict**: https://github.com/alimoradi296/PyConflict
- **Marketplace status**: local VSIX installation only; publishing is not verified
- **Issues**: https://github.com/alimoradi296/PyConflict/issues
- **Documentation**: https://github.com/alimoradi296/PyConflict/tree/main/vscode-extension

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Support

- **Report bugs**: [GitHub Issues](https://github.com/alimoradi296/PyConflict/issues)
- **Ask questions or report issues**: [GitHub Issues](https://github.com/alimoradi296/PyConflict/issues)

---

**Made with ❤️ for Python developers**
