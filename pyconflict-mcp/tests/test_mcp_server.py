"""Offline unit tests for MCP tools and request dispatch."""

import sys

import pytest
from mcp import Client
from pyconflict_mcp import server, tools


@pytest.mark.asyncio
async def test_list_tools_exposes_expected_operations():
    listed = await server.server.list_tools()

    assert {tool.name for tool in listed} == {
        "check_package",
        "get_stable_version",
        "check_environment",
        "batch_check",
    }


@pytest.mark.asyncio
async def test_check_package_preserves_cli_result_without_adding_confidence(monkeypatch):
    calls = []

    async def fake_run(args):
        calls.append(args)
        return {
            "exit_code": 0,
            "package": {"name": "django", "version": "5.0"},
            "conflicts": [],
            "suggestions": [],
            "caveats": [],
        }

    monkeypatch.setattr(tools, "run_pyconflict_command", fake_run)
    result = await tools.check_package(tools.CheckPackageInput(package="django", version="5.0"))

    assert calls == [["check-add", "django", "--json", "--version", "5.0"]]
    assert result["safe"] is True
    assert "confidence" not in result


@pytest.mark.asyncio
async def test_check_environment_preserves_analysis_errors(monkeypatch):
    async def fake_run(args):
        assert args == ["check-env", "--json"]
        return {
            "exit_code": 1,
            "healthy": False,
            "conflicts": [{"dependency": "idna"}],
            "analysis_errors": ["bad metadata"],
            "packages_count": 4,
        }

    monkeypatch.setattr(tools, "run_pyconflict_command", fake_run)
    result = await tools.check_environment(tools.CheckEnvironmentInput())

    assert result == {
        "healthy": False,
        "conflicts": [{"dependency": "idna"}],
        "analysis_errors": ["bad metadata"],
        "packages_count": 4,
    }


@pytest.mark.asyncio
async def test_batch_check_reports_each_package_status(monkeypatch):
    async def fake_check(input_data):
        if input_data.package == "broken":
            raise RuntimeError("CLI unavailable")
        return {
            "safe": False,
            "status": "conflict",
            "conflicts": [{"dependency": "urllib3"}],
        }

    monkeypatch.setattr(tools, "check_package", fake_check)
    request = tools.BatchCheckInput(
        packages=[
            tools.BatchCheckInput.PackageSpec(name="requests"),
            tools.BatchCheckInput.PackageSpec(name="broken"),
        ]
    )

    result = await tools.batch_check(request)

    assert result["results"][0]["status"] == "conflict"
    assert result["results"][0]["safe"] is False
    assert result["results"][1]["status"] == "error"
    assert result["results"][1]["error"] == "CLI unavailable"


@pytest.mark.asyncio
async def test_run_command_keeps_json_on_nonzero_exit(monkeypatch):
    class FakeProcess:
        returncode = 1

        async def communicate(self):
            return b'{"exit_code": 1, "status": "conflict"}', b""

    async def fake_create_subprocess_exec(*args, **kwargs):
        assert args == (
            sys.executable,
            "-m",
            "pyconflict",
            "check-add",
            "django",
            "--json",
        )
        return FakeProcess()

    monkeypatch.setattr(tools.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    result = await tools.run_pyconflict_command(["check-add", "django", "--json"])

    assert result == {"exit_code": 1, "status": "conflict"}


@pytest.mark.asyncio
async def test_server_dispatch_returns_structured_result(monkeypatch):
    async def fake_check(input_data):
        return {"safe": True, "package": {"name": "requests"}}

    monkeypatch.setattr(tools, "check_package", fake_check)
    response = await server.server.call_tool("check_package", {"package": "requests"})

    assert response.structured_content == {
        "safe": True,
        "package": {"name": "requests"},
    }


@pytest.mark.asyncio
async def test_mcp_client_discovers_server_tools():
    async with Client(server.server) as client:
        listed = await client.list_tools()

    assert {tool.name for tool in listed.tools} == {
        "check_package",
        "get_stable_version",
        "check_environment",
        "batch_check",
    }
