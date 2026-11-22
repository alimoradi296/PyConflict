"""Smoke test the installed MCP entry point over a real stdio transport."""

import sys

import pytest
from mcp import Client
from mcp.client.stdio import StdioServerParameters


@pytest.mark.asyncio
async def test_stdio_server_handshake_and_tool_discovery():
    client = Client(
        StdioServerParameters(
            command=sys.executable,
            args=["-m", "pyconflict_mcp.server"],
        ),
        read_timeout_seconds=10,
    )

    async with client:
        result = await client.list_tools()

    assert {tool.name for tool in result.tools} == {
        "check_package",
        "get_stable_version",
        "check_environment",
        "batch_check",
    }
