# PyConflict MCP Server

MCP (Model Context Protocol) server for PyConflict, enabling seamless integration with Claude Code and other AI coding assistants.

## What is MCP?

MCP (Model Context Protocol) is a protocol that allows AI assistants like Claude Code to interact with external tools and services. This server exposes PyConflict's functionality through MCP, enabling Claude to check Python dependency conflicts automatically.

## Features

- **check_package**: Check if adding a package will cause conflicts
- **get_stable_version**: Get the latest stable version of a package
- **check_environment**: Check current environment for conflicts
- **batch_check**: Check multiple packages at once

## Installation

The MCP server is currently distributed as source in this repository and requires Python 3.11 or newer. Install
the core project and MCP package from a clone:

```bash
git clone https://github.com/alimoradi296/PyConflict.git
cd PyConflict
pip install -e .
pip install -e "./pyconflict-mcp"
```

## Usage with Claude Code

### 1. Install the MCP server from the repository

```bash
pip install -e "./pyconflict-mcp"
```

### 2. Configure Claude Code

Add to your Claude Code configuration (`~/.config/claude/mcp_config.json`):

```json
{
  "mcpServers": {
    "pyconflict": {
      "command": "pyconflict-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

### 3. Use in Claude Code

Claude will automatically use PyConflict when working with Python dependencies:

```
User: "Add tensorflow to my project"
Claude: [Internally calls check_package tool]
Claude: "I've checked and tensorflow 2.15.0 is safe to add. Adding it now..."
```

## MCP Tools

### check_package

Check if adding a package will cause conflicts.

**Input:**
```json
{
  "package": "django",
  "version": "3.2.0"  // optional
}
```

**Output:**
```json
{
  "safe": false,
  "conflicts": [
    {
      "dependency": "asgiref",
      "required": ">=3.3.2,<4",
      "installed": "3.7.2"
    }
  ],
  "suggestions": ["Upgrade django to 4.2+"]
}
```

### get_stable_version

Get the latest stable version of a package.

**Input:**
```json
{
  "package": "pandas",
  "python_version": "3.8"  // optional
}
```

**Output:**
```json
{
  "package": "pandas",
  "version": "2.1.4"
}
```

### check_environment

Check current environment for conflicts.

**Input:**
```json
{}
```

**Output:**
```json
{
  "healthy": true,
  "conflicts": [],
  "packages_count": 42
}
```

### batch_check

Check multiple packages at once.

**Input:**
```json
{
  "packages": [
    {"name": "django", "version": "4.2"},
    {"name": "fastapi"},
    {"name": "requests"}
  ]
}
```

**Output:**
```json
{
  "results": [
    {"package": "django", "safe": true},
    {"package": "fastapi", "safe": true},
    {"package": "requests", "safe": true}
  ]
}
```

## Development

### Setup

```bash
git clone https://github.com/alimoradi296/PyConflict.git
cd PyConflict
pip install -e .
pip install -e "./pyconflict-mcp[dev]"
```

### Running Tests

```bash
pytest
```

### Manual Testing

```bash
# Start the MCP server. It waits for MCP stdio messages; it is not a shell CLI.
pyconflict-mcp

# Configure this command in an MCP client to exchange protocol messages.
```

## Architecture

The MCP server is a thin wrapper around the PyConflict CLI:

```
┌──────────────┐
│ Claude Code  │
└──────┬───────┘
       │ MCP Protocol
┌──────▼────────┐
│  MCP Server   │
└──────┬────────┘
       │ subprocess
┌──────▼────────┐
│ PyConflict CLI│
└───────────────┘
```

This design ensures:
- No code duplication
- CLI and MCP stay in sync
- Simple, reliable implementation

## Troubleshooting

### Claude Code doesn't see the tools

1. Check MCP server is installed: `which pyconflict-mcp`
2. Verify configuration: Check `~/.config/claude/mcp_config.json`
3. Restart Claude Code
4. Check logs: `~/.config/claude/mcp_logs/pyconflict.log`

### Permission errors

```bash
chmod +x $(which pyconflict-mcp)
```

## License

MIT License - see LICENSE file for details.

## Links

- **PyConflict**: https://github.com/alimoradi296/PyConflict
- **MCP Documentation**: https://modelcontextprotocol.io
- **Claude Code**: https://claude.ai/code
