"""Output formatters for CLI."""

import json
from typing import Any, Dict

from rich.console import Console
from rich.table import Table

from pyconflict.application.use_cases.check_add_package import CheckAddPackageResponse
from pyconflict.application.use_cases.get_latest_stable import GetLatestStableResponse


class HumanFormatter:
    """Format output for human-readable terminal display."""

    def __init__(self) -> None:
        """Initialize the formatter."""
        self._console = Console()

    def format_check_add(self, response: CheckAddPackageResponse) -> str:
        """Format check-add response.

        Args:
            response: The response to format

        Returns:
            Formatted string
        """
        lines = []

        if response.safe_to_add:
            lines.append(
                f"[green]✓[/green] Safe to add {response.package.name}=={response.package.version}"
            )
            lines.append(f"  Confidence: {response.confidence * 100:.0f}%")
        else:
            lines.append(
                f"[red]✗[/red] Cannot add {response.package.name}=={response.package.version}"
            )
            lines.append("")
            lines.append("[bold]Conflicts detected:[/bold]")

            for conflict in response.conflicts:
                lines.append(f"  [red]•[/red] {conflict.dependency_name}")
                lines.append(f"    Required: {conflict.required_constraint}")
                if conflict.installed_version:
                    lines.append(f"    Installed: {conflict.installed_version}")

            if response.suggestions:
                lines.append("")
                lines.append("[bold]Suggestions:[/bold]")
                for suggestion in response.suggestions:
                    lines.append(f"  [yellow]→[/yellow] {suggestion}")

        if response.caveats:
            lines.append("")
            lines.append("[dim]Caveats:[/dim]")
            for caveat in response.caveats:
                lines.append(f"  [dim]ℹ {caveat}[/dim]")

        # Use Rich to render with colors
        output = "\n".join(lines)
        return output

    def format_latest_stable(self, response: GetLatestStableResponse) -> str:
        """Format latest-stable response.

        Args:
            response: The response to format

        Returns:
            Formatted string
        """
        output = f"{response.package_name}=={response.version}"

        if response.is_filtered_by_python:
            output += " [dim](filtered by Python version)[/dim]"

        return output


class JSONFormatter:
    """Format output as JSON for machine consumption."""

    @staticmethod
    def format_check_add(response: CheckAddPackageResponse) -> str:
        """Format check-add response as JSON.

        Args:
            response: The response to format

        Returns:
            JSON string
        """
        data: Dict[str, Any] = {
            "status": "safe" if response.safe_to_add else "conflict",
            "exit_code": 0 if response.safe_to_add else 1,
            "package": {
                "name": response.package.name,
                "version": str(response.package.version),
            },
            "conflicts": [
                {
                    "dependency": c.dependency_name,
                    "required": str(c.required_constraint),
                    "installed": str(c.installed_version) if c.installed_version else None,
                    "required_by": c.required_by,
                    "severity": c.severity.value,
                }
                for c in response.conflicts
            ],
            "suggestions": response.suggestions,
            "confidence": response.confidence,
            "caveats": response.caveats,
        }

        return json.dumps(data, indent=2)

    @staticmethod
    def format_latest_stable(response: GetLatestStableResponse) -> str:
        """Format latest-stable response as JSON.

        Args:
            response: The response to format

        Returns:
            JSON string
        """
        data = {
            "package": response.package_name,
            "version": str(response.version),
            "is_filtered_by_python": response.is_filtered_by_python,
        }

        return json.dumps(data, indent=2)
