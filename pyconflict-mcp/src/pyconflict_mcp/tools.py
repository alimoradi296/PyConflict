"""MCP Tools for PyConflict."""

import asyncio
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CheckPackageInput(BaseModel):
    """Input for check_package tool."""

    package: str = Field(description="Package name to check")
    version: Optional[str] = Field(default=None, description="Specific version to check")


class GetStableVersionInput(BaseModel):
    """Input for get_stable_version tool."""

    package: str = Field(description="Package name")
    python_version: Optional[str] = Field(default=None, description="Python version to filter by")


class CheckEnvironmentInput(BaseModel):
    """Input for check_environment tool."""

    pass


class BatchCheckInput(BaseModel):
    """Input for batch_check tool."""

    class PackageSpec(BaseModel):
        """Single package specification."""

        name: str
        version: Optional[str] = None

    packages: List[PackageSpec] = Field(description="List of packages to check")


async def run_pyconflict_command(args: List[str]) -> Dict[str, Any]:
    """
    Run a pyconflict command and return the result.

    Args:
        args: Command arguments (e.g., ["check-add", "django", "--json"])

    Returns:
        Command result as dictionary

    Raises:
        subprocess.SubprocessError: If command fails
    """
    cmd = [sys.executable, "-m", "pyconflict"] + args

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode is None:
        raise subprocess.SubprocessError("Process did not terminate")

    # Try to parse JSON output
    try:
        result = json.loads(stdout.decode())
        result["exit_code"] = process.returncode
        return result
    except json.JSONDecodeError:
        # If not JSON, return raw output
        return {
            "exit_code": process.returncode,
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
        }


async def check_package(input_data: CheckPackageInput) -> Dict[str, Any]:
    """
    Check if adding a package will cause conflicts.

    Args:
        input_data: Package specification

    Returns:
        Check result with conflicts and suggestions
    """
    args = ["check-add", input_data.package, "--json"]
    if input_data.version:
        args.extend(["--version", input_data.version])

    result = await run_pyconflict_command(args)

    # Transform to MCP-friendly format
    return {
        "safe": result.get("exit_code") == 0,
        "package": result.get("package", {}),
        "conflicts": result.get("conflicts", []),
        "suggestions": result.get("suggestions", []),
        "caveats": result.get("caveats", []),
        "error": result.get("error"),
    }


async def get_stable_version(input_data: GetStableVersionInput) -> Dict[str, Any]:
    """
    Get the latest stable version of a package.

    Args:
        input_data: Package name and optional Python version

    Returns:
        Package name and latest stable version
    """
    args = ["stable", input_data.package, "--json"]
    if input_data.python_version:
        args.extend(["--python-version", input_data.python_version])

    result = await run_pyconflict_command(args)

    return {
        "package": result.get("package"),
        "version": result.get("version"),
        "filtered": result.get("filtered", False),
    }


async def check_environment(input_data: CheckEnvironmentInput) -> Dict[str, Any]:
    """
    Check current environment for conflicts.

    Args:
        input_data: Empty input

    Returns:
        Environment health status
    """
    args = ["check-env", "--json"]
    result = await run_pyconflict_command(args)

    return {
        "healthy": result.get("exit_code") == 0,
        "conflicts": result.get("conflicts", []),
        "analysis_errors": result.get("analysis_errors", []),
        "packages_count": result.get("packages_count", 0),
    }


async def batch_check(input_data: BatchCheckInput) -> Dict[str, Any]:
    """
    Check multiple packages at once.

    Args:
        input_data: List of packages to check

    Returns:
        Results for all packages
    """
    results = []

    for pkg_spec in input_data.packages:
        try:
            check_input = CheckPackageInput(package=pkg_spec.name, version=pkg_spec.version)
            result = await check_package(check_input)
            results.append(
                {
                    "package": pkg_spec.name,
                    "version": pkg_spec.version,
                    "safe": result["safe"],
                    "status": result.get("status", "safe" if result["safe"] else "conflict"),
                    "conflicts": result.get("conflicts", []),
                }
            )
        except Exception as e:
            results.append(
                {
                    "package": pkg_spec.name,
                    "safe": False,
                    "status": "error",
                    "error": str(e),
                }
            )

    return {"results": results}
