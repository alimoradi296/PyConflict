"""Suggestion generation for conflict resolution."""

from typing import List

from pyconflict.domain.entities import Conflict, Environment, Package
from pyconflict.domain.services.version_resolver import VersionResolver


class SuggestionGenerator:
    """Domain service for generating conflict resolution suggestions."""

    def __init__(self, version_resolver: VersionResolver) -> None:
        """Initialize the suggestion generator.

        Args:
            version_resolver: Version resolution service
        """
        self._version_resolver = version_resolver

    def generate(
        self, package: Package, conflicts: List[Conflict], environment: Environment
    ) -> List[str]:
        """Generate suggestions for resolving conflicts.

        Args:
            package: The package being added
            conflicts: List of detected conflicts
            environment: Current environment

        Returns:
            List of human-readable suggestions
        """
        if not conflicts:
            return []

        suggestions = []

        # MVP: Simple suggestions
        # Phase 2: More sophisticated resolution strategies
        for conflict in conflicts:
            suggestion = self._generate_conflict_suggestion(conflict, package)
            if suggestion:
                suggestions.append(suggestion)

        # Add general advice
        if len(conflicts) > 1:
            suggestions.append(
                f"Consider upgrading {package.name} to a newer version that may have "
                "more compatible dependencies"
            )

        return suggestions

    def _generate_conflict_suggestion(
        self, conflict: Conflict, package: Package
    ) -> str:
        """Generate a suggestion for a single conflict.

        Args:
            conflict: The conflict
            package: The package being added

        Returns:
            A suggestion string
        """
        dep_name = conflict.dependency_name
        required = conflict.required_constraint
        installed = conflict.installed_version

        if installed and required:
            # Check if upgrade or downgrade needed
            if str(required).startswith(">="):
                # Need to upgrade installed version
                return (
                    f"Upgrade '{dep_name}' from {installed} to satisfy "
                    f"{package.name}'s requirement ({required})"
                )
            elif str(required).startswith("<"):
                # Need to downgrade or find compatible version
                return (
                    f"'{dep_name}' version {installed} is too new for {package.name} "
                    f"(requires {required}). Consider using an older version of {package.name}"
                )
            else:
                # Complex constraint
                return (
                    f"'{dep_name}' version {installed} doesn't satisfy {package.name}'s "
                    f"requirement ({required}). Check for compatible versions"
                )

        return f"Resolve '{dep_name}' version conflict manually"
