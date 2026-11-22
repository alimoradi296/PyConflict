"""Use case for checking if a package can be added safely."""

from dataclasses import dataclass
from typing import List, Optional

from pyconflict.domain.entities import Conflict, Environment, Package
from pyconflict.domain.repositories import IEnvironmentRepository, IPackageRepository
from pyconflict.domain.services.conflict_detector import ConflictDetector
from pyconflict.domain.services.suggestion_generator import SuggestionGenerator


@dataclass
class CheckAddPackageRequest:
    """Request to check if a package can be added."""

    package_name: str
    version: Optional[str] = None


@dataclass
class CheckAddPackageResponse:
    """Response from checking a package."""

    safe_to_add: bool
    package: Package
    conflicts: List[Conflict]
    suggestions: List[str]
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

        # 5. Describe checks that are not part of the current analysis.
        caveats = self._get_caveats()

        return CheckAddPackageResponse(
            safe_to_add=len(conflicts) == 0,
            package=package,
            conflicts=conflicts,
            suggestions=suggestions,
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

    def _get_caveats(self) -> List[str]:
        """List limitations of this check.

        Returns:
            List of caveats/warnings about what wasn't checked
        """
        return [
            "Only direct dependencies checked (not transitive)",
            "Optional extras not included",
        ]
