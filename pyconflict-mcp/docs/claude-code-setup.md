# Configure the PyConflict MCP server

The MCP server is source-distributed in this repository and requires Python 3.11 or newer.

## Install from a clone

Use the same virtual environment for both packages:

```bash
git clone https://github.com/alimoradi296/PyConflict.git
cd PyConflict
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install -e ./pyconflict-mcp
```

The MCP server starts as a stdio process. It does not have a shell `--help` command. Configure the absolute path to the installed `pyconflict-mcp` executable in your MCP client so it uses this virtual environment.

## Claude Code configuration

Add a server entry to the MCP configuration used by your Claude Code installation. For example:

```json
{
  "mcpServers": {
    "pyconflict": {
      "command": "/absolute/path/to/PyConflict/.venv/bin/pyconflict-mcp",
      "args": []
    }
  }
}
```

Use the configuration path documented by the installed Claude Code version. Keep the absolute executable path aligned with the virtual environment where both packages are installed.

## Verify

Run the MCP package tests from the repository root:

```bash
python -m pip install -e "./pyconflict-mcp[dev]"
python -m pytest pyconflict-mcp/tests -q
```

The tests check tool discovery, tool dispatch, and CLI result mapping without making PyPI requests.

The MCP server exposes package checking, stable-version lookup, environment checking, and batch checking. It does not expose the optional Redis team baseline command.
