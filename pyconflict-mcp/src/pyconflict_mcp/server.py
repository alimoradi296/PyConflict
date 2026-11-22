"""MCP server exposing the PyConflict CLI checks as typed tools."""

from typing import Any, Optional

from mcp.server import MCPServer
from pydantic import BaseModel

from . import tools

server = MCPServer("pyconflict")


class PackageInput(BaseModel):
    """One package and an optional exact version."""

    name: str
    version: Optional[str] = None


@server.tool(name="check_package")
async def check_package(package: str, version: Optional[str] = None) -> dict[str, Any]:
    """Check whether adding a package conflicts with the active environment."""
    request = tools.CheckPackageInput(package=package, version=version)
    return await tools.check_package(request)


@server.tool(name="get_stable_version")
async def get_stable_version(package: str, python_version: Optional[str] = None) -> dict[str, Any]:
    """Find the latest stable version compatible with an optional Python version."""
    request = tools.GetStableVersionInput(package=package, python_version=python_version)
    return await tools.get_stable_version(request)


@server.tool(name="check_environment")
async def check_environment() -> dict[str, Any]:
    """Check the active Python environment for requirement conflicts."""
    return await tools.check_environment(tools.CheckEnvironmentInput())


@server.tool(name="batch_check")
async def batch_check(packages: list[PackageInput]) -> dict[str, Any]:
    """Check multiple package names or exact version pins."""
    request = tools.BatchCheckInput(
        packages=[
            tools.BatchCheckInput.PackageSpec(name=item.name, version=item.version)
            for item in packages
        ]
    )
    return await tools.batch_check(request)


def main() -> None:
    """Run the MCP server over standard input and output."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
