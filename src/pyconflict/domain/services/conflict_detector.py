"""Conflict detection logic."""

import sys
from typing import List, Optional

from packaging.markers import Marker

from pyconflict.domain.entities import (
    Conflict,
    ConflictSeverity,
    Dependency,
    Environment,
    Package,
)
from pyconflict.domain.services.version_resolver import VersionResolver


class ConflictDetector:
    """Domain service for detecting dependency conflicts.

    Pure business logic for checking if a package's dependencies
    are compatible with the current environment.
    """

    def __init__(self, version_resolver: Optional[VersionResolver] = None) -> None:
        """Initialize the conflict detector.

        Args:
            version_resolver: Version resolution service
        """
        self._version_resolver = version_resolver or VersionResolver()

    def detect_conflicts(self, package: Package, environment: Environment) -> List[Conflict]:
        """Detect conflicts between a package and the environment.

        Args:
            package: The package to check
            environment: The current environment state

        Returns:
            List of detected conflicts
        """
        conflicts = []

        for dep in package.dependencies:
            # MVP: Skip platform markers check (Phase 2 feature)
            # if not self._should_check_dependency(dep, environment):
            #     continue

            conflict = self._check_dependency(dep, package, environment)
            if conflict:
                conflicts.append(conflict)

        return conflicts

    def _should_check_dependency(self, dep: Dependency, env: Environment) -> bool:
        """Check if a dependency applies to this environment.

        Evaluates PEP 508 markers to determine if the dependency
        should be installed on this platform/Python version.

        Args:
            dep: The dependency to check
            env: The environment

        Returns:
            True if dependency should be checked, False otherwise
        """
        if not dep.markers:
            return True

        try:
            marker = Marker(dep.markers)
            # Build evaluation context
            context = {
                "python_version": f"{env.python_version.major}.{env.python_version.minor}",
                "python_full_version": str(env.python_version),
                "sys_platform": env.platform,
                "platform_system": sys.platform,
            }
            return marker.evaluate(context)
        except Exception:
            # If marker evaluation fails, assume dependency applies
            # Better to check and warn than to miss a conflict
            return True

    def _check_dependency(
        self, dep: Dependency, package: Package, env: Environment
    ) -> Optional[Conflict]:
        """Check a single dependency for conflicts.

        Args:
            dep: The dependency to check
            package: The package that requires this dependency
            env: The environment

        Returns:
            A Conflict if incompatible, None otherwise
        """
        installed_version = env.get_version(dep.name)

        # If dependency not installed, no conflict
        # (it will be installed when the package is installed)
        if not installed_version:
            return None

        # Check if installed version satisfies the constraint
        if self._version_resolver.is_compatible(installed_version, dep.specifier):
            return None

        # Conflict detected
        return Conflict(
            dependency_name=dep.name,
            required_by=str(package),
            required_constraint=dep.specifier,
            installed_version=installed_version,
            conflicting_package=None,  # MVP: Don't track which package installed it
            severity=ConflictSeverity.ERROR,
        )
