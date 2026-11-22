"""CLI commands using Typer."""

import json as json_lib
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from packaging.requirements import InvalidRequirement, Requirement
from rich.console import Console

from pyconflict.application.exceptions import PackageNotFoundError, RepositoryError
from pyconflict.application.use_cases.check_add_package import CheckAddPackageRequest
from pyconflict.application.use_cases.get_latest_stable import GetLatestStableRequest
from pyconflict.presentation.cli.di import (
    get_check_add_package_use_case,
    get_check_environment_use_case,
    get_environment_repository,
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
    package: str = typer.Argument(
        ..., help="Package name to check (e.g., 'django' or 'django==3.2')"
    ),
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
    request = CheckAddPackageRequest(package_name=pkg_name, version=pkg_version, check_deep=deep)

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
    request = GetLatestStableRequest(package_name=package, python_version=python_version)

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


@app.command(name="check-env")
def check_env(
    output_json: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Check current environment for dependency conflicts.

    Examples:

        pyconflict check-env

        pyconflict check-env --json
    """
    try:
        response = get_check_environment_use_case().execute()
        conflicts = [
            {
                "dependency": conflict.dependency_name,
                "required": str(conflict.required_constraint) or "any version",
                "installed": (
                    str(conflict.installed_version)
                    if conflict.installed_version is not None
                    else None
                ),
                "required_by": conflict.required_by,
                "severity": conflict.severity.value,
            }
            for conflict in response.conflicts
        ]
        analysis_errors = response.analysis_errors

        if output_json:
            result = {
                "healthy": len(conflicts) == 0 and not analysis_errors,
                "conflicts": conflicts,
                "analysis_errors": analysis_errors,
                "packages_count": response.packages_count,
                "exit_code": response.exit_code,
            }
            typer.echo(json_lib.dumps(result, indent=2))
        else:
            if conflicts:
                console.print(f"[red]✗[/red] {len(conflicts)} dependency issues detected")
                for conflict in conflicts:
                    installed = conflict["installed"] or "not installed"
                    console.print(
                        f"  • {conflict['required_by']} requires {conflict['dependency']} "
                        f"{conflict['required']}; found {installed}"
                    )
            elif not analysis_errors:
                console.print("[green]✓[/green] Environment healthy - no conflicts detected")
            else:
                console.print("[yellow]![/yellow] Environment check could not analyze all metadata")
            console.print(f"  Total packages: {response.packages_count}")
            if analysis_errors:
                console.print(f"  Metadata errors: {len(analysis_errors)}")

        raise typer.Exit(code=response.exit_code)

    except typer.Exit:
        raise
    except Exception as e:
        _handle_error(f"Error checking environment: {e}", output_json, exit_code=5)


@app.command(name="batch-check")
def batch_check(
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="File containing package names (one per line)"
    ),
    packages: Optional[List[str]] = typer.Option(
        None,
        "--package",
        "-p",
        help="Package names to check (can be used multiple times)",
    ),
    output_json: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Check package names or exact ``name==version`` pins in one call.

    Examples:

        pyconflict batch-check --file packages.txt

        pyconflict batch-check -p django -p fastapi -p celery

        pyconflict batch-check --file packages.txt --json
    """
    # Collect packages from file and/or command line
    pkg_list = []

    if file:
        try:
            with open(file) as f:
                pkg_list.extend([line.strip() for line in f if line.strip()])
        except FileNotFoundError:
            _handle_error(f"File not found: {file}", output_json, exit_code=2)
            return
        except Exception as e:
            _handle_error(f"Error reading file: {e}", output_json, exit_code=5)
            return

    if packages:
        pkg_list.extend(packages)

    if not pkg_list:
        _handle_error(
            "No packages specified. Use --file or --package option.",
            output_json,
            exit_code=2,
        )
        return

    # Check each package. This command supports a name or an exact == pin only.
    results: List[Dict[str, Any]] = []
    batch_exit_code = 0
    for pkg_spec in pkg_list:
        try:
            requirement = Requirement(pkg_spec)
            if requirement.extras or requirement.marker:
                raise ValueError("extras and environment markers are not supported")
            specifier = next(iter(requirement.specifier), None)
            if specifier and (
                len(requirement.specifier) != 1
                or specifier.operator != "=="
                or "*" in specifier.version
            ):
                raise ValueError("only an exact == version pin is supported")
            pkg_name = requirement.name
            pkg_version = specifier.version if specifier else None
        except (InvalidRequirement, ValueError, StopIteration) as e:
            batch_exit_code = max(batch_exit_code, 2)
            results.append(
                {
                    "package": pkg_spec,
                    "safe": False,
                    "status": "error",
                    "exit_code": 2,
                    "error": str(e),
                }
            )
            continue

        try:
            request = CheckAddPackageRequest(package_name=pkg_name, version=pkg_version)
            use_case = get_check_add_package_use_case()
            response = use_case.execute(request)

            results.append(
                {
                    "package": pkg_name,
                    "version": pkg_version or str(response.package.version),
                    "safe": response.safe_to_add,
                    "status": "safe" if response.safe_to_add else "conflict",
                    "conflicts": [
                        {
                            "dependency": c.dependency_name,
                            "required": str(c.required_constraint) or "any version",
                            "installed": (
                                str(c.installed_version)
                                if c.installed_version is not None
                                else None
                            ),
                        }
                        for c in response.conflicts
                    ],
                }
            )
        except PackageNotFoundError as e:
            error_code = 2
            results.append(
                {
                    "package": pkg_name,
                    "safe": False,
                    "status": "error",
                    "exit_code": error_code,
                    "error": str(e),
                }
            )
        except RepositoryError as e:
            error_code = 4
            results.append(
                {
                    "package": pkg_name,
                    "safe": False,
                    "status": "error",
                    "exit_code": error_code,
                    "error": str(e),
                }
            )
        except Exception as e:
            error_code = 5
            results.append(
                {
                    "package": pkg_name,
                    "safe": False,
                    "status": "error",
                    "exit_code": error_code,
                    "error": str(e),
                }
            )
        else:
            error_code = 0
        batch_exit_code = max(batch_exit_code, error_code)
        if results[-1].get("status") == "conflict":
            batch_exit_code = max(batch_exit_code, 1)

    # Output results
    if output_json:
        output = {
            "results": results,
            "total": len(results),
            "exit_code": batch_exit_code,
        }
        typer.echo(json_lib.dumps(output, indent=2))
    else:
        safe_count = sum(1 for r in results if r.get("safe"))
        conflict_count = sum(1 for result in results if result.get("status") == "conflict")
        error_count = len(results) - safe_count - conflict_count

        console.print("\n[bold]Batch Check Results:[/bold]")
        console.print(f"  Total packages: {len(results)}")
        console.print(f"  [green]Safe:[/green] {safe_count}")
        console.print(f"  [red]Conflicts:[/red] {conflict_count}\n")
        console.print(f"  Errors: {error_count}\n")

        for result in results:
            pkg = result["package"]
            if result.get("safe"):
                console.print(f"[green]✓[/green] {pkg} - Safe to add")
            elif result.get("status") == "conflict":
                console.print(f"[red]✗[/red] {pkg} - Conflicts detected")
                if "error" in result:
                    console.print(f"    Error: {result['error']}")
            else:
                console.print(f"[yellow]![/yellow] {pkg} - Could not check")
                console.print(f"    Error: {result.get('error', 'Unknown error')}")

    raise typer.Exit(code=batch_exit_code)


@app.command(name="team-check")
def team_check(
    workspace_id: str = typer.Option(..., envvar="PYCONFLICT_WORKSPACE_ID"),
    redis_url: str = typer.Option(..., envvar="PYCONFLICT_REDIS_URL"),
    set_standard: bool = typer.Option(
        False,
        "--set-standard",
        help="Explicitly save this environment as the shared team baseline",
    ),
    output_json: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Compare this environment with a Redis team baseline.

    Saving a baseline uploads package names and versions from this environment.
    That upload only occurs when ``--set-standard`` is supplied.
    """
    try:
        from pyconflict.application.use_cases.team_check import TeamCheckUseCase
        from pyconflict.infrastructure.repositories.cloud_cache_repository import (
            CloudCacheRepository,
        )

        environment = get_environment_repository()
        cache = CloudCacheRepository(redis_url=redis_url, workspace_id=workspace_id)
        use_case = TeamCheckUseCase(environment, cache, workspace_id)

        result: Dict[str, Any]
        if set_standard:
            standard = use_case.save_current_as_standard()
            result = {
                "workspace_id": workspace_id,
                "saved": True,
                "packages_count": len(standard),
                "exit_code": 0,
            }
        else:
            checked = use_case.execute()
            result = {
                "workspace_id": checked.workspace_id,
                "matches_standard": checked.matches_standard,
                "drift": checked.drift,
                "packages_count": checked.packages_count,
                "exit_code": 0 if checked.matches_standard else 1,
            }

        if output_json:
            typer.echo(json_lib.dumps(result, indent=2))
        elif set_standard:
            console.print(
                f"Saved {result['packages_count']} package versions to workspace {workspace_id}."
            )
        elif result["matches_standard"]:
            console.print("[green]✓[/green] Environment matches the team baseline.")
        else:
            console.print(f"[yellow]![/yellow] {len(result['drift'])} package differences found.")
            for item in result["drift"]:
                console.print(
                    f"  {item['status']}: {item['package']} "
                    f"(installed={item['installed_version']}, "
                    f"standard={item['standard_version']})"
                )
        raise typer.Exit(code=result["exit_code"])
    except typer.Exit:
        raise
    except Exception as error:
        _handle_error(f"Team check failed: {error}", output_json, exit_code=5)


def _handle_error(message: str, output_json: bool, exit_code: int) -> None:
    """Handle and format an error.

    Args:
        message: Error message
        output_json: Whether to output as JSON
        exit_code: Exit code to use
    """
    if output_json:
        error_data = {"error": message, "exit_code": exit_code}
        typer.echo(json_lib.dumps(error_data, indent=2), err=True)
    else:
        console.print(f"[red]Error:[/red] {message}")

    raise typer.Exit(code=exit_code)


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        from pyconflict import __version__

        typer.echo(f"PyConflict version {__version__}")
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
