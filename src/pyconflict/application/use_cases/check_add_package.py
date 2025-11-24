"""Use case for checking if a package can be added safely."""

import sys
from dataclasses import dataclass
from typing import List, Optional

from packaging.version import Version

from pyconflict.domain.entities import Conflict, Environment, Package
from pyconflict.domain.repositories import IEnvironmentRepository, IPackageRepository
from pyconflict.domain.services.conflict_detector import ConflictDetector
from pyconflict.domain.services.suggestion_generator import SuggestionGenerator


@dataclass
class CheckAddPackageRequest:
    """Request to check if a package can be added."""

    package_name: str
    version: Optional[str] = None
    check_deep: bool = False  # Phase 3: transitive dependencies


@dataclass
class CheckAddPackageResponse:
    """Response from checking a package."""

    safe_to_add: bool
    package: Package
    conflicts: List[Conflict]
    suggestions: List[str]
    confidence: float
    caveats: List[str]


class CheckAddPackageUseCase:
    """Use case: Check if adding a package will cause conflicts.

    This is the core use case of PyConflict - answering the question:
    "Will adding this package break my environment?"
    """

    def __init__(
        self,
        package_repo: IPackageRepository,
        env_repo: IEnvironmentRepository,
        conflict_detector: ConflictDetector,
        suggestion_generator: SuggestionGenerator,
    ) -> None:
        """Initialize the use case.

        Args:
            package_repo: Repository for fetching package metadata
            env_repo: Repository for reading environment state
            conflict_detector: Service for detecting conflicts
            suggestion_generator: Service for generating suggestions
        """
        self._package_repo = package_repo
        self._env_repo = env_repo
        self._conflict_detector = conflict_detector
        self._suggestion_generator = suggestion_generator

    def execute(self, request: CheckAddPackageRequest) -> CheckAddPackageResponse:
        """Execute the use case.

        Args:
            request: The request parameters

        Returns:
            Response with conflict analysis
        """
        # 1. Get current environment state
        environment = self._get_environment()

        # 2. Fetch target package metadata
        package = self._package_repo.get_package(request.package_name, request.version)

        # 3. Detect conflicts using domain logic
        conflicts = self._conflict_detector.detect_conflicts(package, environment)

        # 4. Generate suggestions if conflicts found
        suggestions = []
        if conflicts:
            suggestions = self._suggestion_generator.generate(package, conflicts, environment)

        # 5. Calculate confidence score
        confidence = self._calculate_confidence(package, environment, request.check_deep)

        # 6. Generate caveats
        caveats = self._get_caveats(request)

        return CheckAddPackageResponse(
            safe_to_add=len(conflicts) == 0,
            package=package,
            conflicts=conflicts,
            suggestions=suggestions,
            confidence=confidence,
            caveats=caveats,
        )

    def _get_environment(self) -> Environment:
        """Get the current environment state.

        Returns:
            Environment entity
        """
        return Environment(
            packages=self._env_repo.get_installed_packages(),
            python_version=self._env_repo.get_python_version(),
            platform=self._env_repo.get_platform(),
        )

    def _calculate_confidence(
        self, package: Package, env: Environment, check_deep: bool
    ) -> float:
        """Calculate confidence in the result.

        Confidence is based on what was checked:
        - Direct dependencies only: 90%
        - With platform markers: 85%
        - With transitive deps: 80%

        Args:
            package: The package being checked
            env: The environment
            check_deep: Whether transitive deps were checked

        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.90  # MVP: Direct dependencies only

        # Phase 2: Account for platform markers
        # has_platform_markers = any(dep.markers for dep in package.dependencies)
        # if has_platform_markers:
        #     confidence *= 0.95

        # Phase 3: Account for transitive dependencies
        if check_deep:
            confidence *= 0.90

        return round(confidence, 2)

    def _get_caveats(self, request: CheckAddPackageRequest) -> List[str]:
        """List limitations of this check.

        Args:
            request: The request

        Returns:
            List of caveats/warnings about what wasn't checked
        """
        caveats = []

        # MVP limitations
        caveats.append("Only direct dependencies checked (not transitive)")
        caveats.append("Platform-specific markers not evaluated")
        caveats.append("Optional extras not included")

        # Add more specific caveats
        if not request.check_deep:
            caveats.append("Use --deep for transitive dependency checking (Phase 3)")

        return caveats
