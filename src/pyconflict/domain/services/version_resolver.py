"""Version resolution logic."""

from typing import List, Optional

from packaging.specifiers import SpecifierSet
from packaging.version import Version


class VersionResolver:
    """Domain service for version constraint resolution.

    Handles version compatibility checks and constraint resolution
    using PEP 440 version semantics.
    """

    def is_compatible(self, version: Version, constraint: SpecifierSet) -> bool:
        """Check if a version satisfies a constraint.

        Args:
            version: The version to check
            constraint: The constraint to check against

        Returns:
            True if version satisfies constraint, False otherwise
        """
        if not constraint:  # Empty constraint means any version
            return True
        return version in constraint

    def find_overlapping_range(
        self, constraints: List[SpecifierSet]
    ) -> Optional[SpecifierSet]:
        """Find the overlapping range of multiple constraints.

        Args:
            constraints: List of version constraints

        Returns:
            A single SpecifierSet representing the intersection,
            or None if constraints are incompatible
        """
        if not constraints:
            return SpecifierSet("")

        # Combine all constraints
        # SpecifierSet handles intersection automatically
        combined_specs = []
        for constraint in constraints:
            combined_specs.extend(str(spec) for spec in constraint)

        if not combined_specs:
            return SpecifierSet("")

        try:
            return SpecifierSet(",".join(combined_specs))
        except Exception:
            # Invalid combination
            return None

    def get_latest_compatible(
        self, versions: List[Version], constraint: SpecifierSet
    ) -> Optional[Version]:
        """Get the latest version that satisfies a constraint.

        Args:
            versions: List of available versions
            constraint: The constraint to satisfy

        Returns:
            The latest compatible version, or None if no match
        """
        compatible = [v for v in versions if self.is_compatible(v, constraint)]

        if not compatible:
            return None

        return max(compatible)

    def filter_stable_versions(self, versions: List[Version]) -> List[Version]:
        """Filter out prerelease versions.

        Args:
            versions: List of versions

        Returns:
            List of stable (non-prerelease) versions
        """
        return [v for v in versions if not v.is_prerelease]
