"""CLI commands using Typer."""

import sys
from typing import Optional

import typer
from rich.console import Console

from pyconflict.application.exceptions import PackageNotFoundError, RepositoryError
from pyconflict.application.use_cases.check_add_package import CheckAddPackageRequest
from pyconflict.application.use_cases.get_latest_stable import GetLatestStableRequest
from pyconflict.presentation.cli.di import (
    get_check_add_package_use_case,
    get_latest_stable_use_case,
)
from pyconflict.presentation.cli.formatters import HumanFormatter, JSONFormatter

app = typer.Typer(
    name="pyconflict",
    help="PyConflict - Python Dependency Conflict Checker. Check if adding a package will cause conflicts before installation.",
    add_completion=True,
)
console = Console()


@app.command(name="check-add")
def check_add(
    package: str = typer.Argument(..., help="Package name to check (e.g., 'django' or 'django==3.2')"),
    version: Optional[str] = typer.Option(None, "--version", help="Specific version to check"),
    output_json: bool = typer.Option(False, "--json", help="Output in JSON format"),
    deep: bool = typer.Option(
        False,
        "--deep",
        help="Check transitive dependencies (Phase 3, not yet implemented)",
    ),
) -> None:
    """Check if adding a package will cause conflicts.

    Examples:

        pyconflict check-add tensorflow

        pyconflict check-add django==3.2

        pyconflict check-add requests --json
    """
    # Parse package name and version if provided as "package==version"
    pkg_name = package
    pkg_version = version

    if "==" in package and version is None:
        parts = package.split("==", 1)
        pkg_name = parts[0]
        pkg_version = parts[1] if len(parts) > 1 else None

    # Build request
    request = CheckAddPackageRequest(
        package_name=pkg_name, version=pkg_version, check_deep=deep
    )

    # Execute use case
    try:
        use_case = get_check_add_package_use_case()
        response = use_case.execute(request)
    except PackageNotFoundError as e:
        _handle_error(f"Package not found: {e.package_name}", output_json, exit_code=2)
        return
    except RepositoryError as e:
        _handle_error(f"Repository error: {e}", output_json, exit_code=4)
        return
    except Exception as e:
        _handle_error(f"Unexpected error: {e}", output_json, exit_code=5)
        return

    # Format output
    if output_json:
        output = JSONFormatter.format_check_add(response)
        typer.echo(output)
    else:
        formatter = HumanFormatter()
        output = formatter.format_check_add(response)
        console.print(output)

    # Exit with appropriate code
    exit_code = 0 if response.safe_to_add else 1
    raise typer.Exit(code=exit_code)


@app.command(name="stable")
def stable(
    package: str = typer.Argument(..., help="Package name (e.g., 'pandas')"),
    python_version: Optional[str] = typer.Option(
        None,
        "--python-version",
        help="Filter by Python version (e.g., '3.8')",
    ),
    output_json: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Get the latest stable version of a package.

    Examples:

        pyconflict stable pandas

        pyconflict stable numpy --python-version 3.8

        pyconflict stable django --json
    """
    # Build request
    request = GetLatestStableRequest(
        package_name=package, python_version=python_version
    )

    # Execute use case
    try:
        use_case = get_latest_stable_use_case()
        response = use_case.execute(request)
    except PackageNotFoundError as e:
        _handle_error(f"Package not found: {e.package_name}", output_json, exit_code=2)
        return
    except RepositoryError as e:
        _handle_error(f"Repository error: {e}", output_json, exit_code=4)
        return
    except Exception as e:
        _handle_error(f"Unexpected error: {e}", output_json, exit_code=5)
        return

    # Format output
    if output_json:
        output = JSONFormatter.format_latest_stable(response)
        typer.echo(output)
    else:
        formatter = HumanFormatter()
        output = formatter.format_latest_stable(response)
        console.print(output)

    raise typer.Exit(code=0)


def _handle_error(message: str, output_json: bool, exit_code: int) -> None:
    """Handle and format an error.

    Args:
        message: Error message
        output_json: Whether to output as JSON
        exit_code: Exit code to use
    """
    if output_json:
        import json

        error_data = {"error": message, "exit_code": exit_code}
        typer.echo(json.dumps(error_data, indent=2), err=True)
    else:
        console.print(f"[red]Error:[/red] {message}")

    raise typer.Exit(code=exit_code)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        typer.echo("PyConflict version 0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """PyConflict - Python Dependency Conflict Checker."""
    pass


if __name__ == "__main__":
    app()
