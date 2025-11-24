"""Dependency injection container for CLI."""

from pathlib import Path

from platformdirs import user_cache_dir

from pyconflict.application.use_cases.check_add_package import CheckAddPackageUseCase
from pyconflict.application.use_cases.get_latest_stable import GetLatestStableUseCase
from pyconflict.domain.services.conflict_detector import ConflictDetector
from pyconflict.domain.services.suggestion_generator import SuggestionGenerator
from pyconflict.domain.services.version_resolver import VersionResolver
from pyconflict.infrastructure.repositories.disk_cache_repository import (
    DiskCacheRepository,
)
from pyconflict.infrastructure.repositories.pip_environment_repository import (
    PipEnvironmentRepository,
)
from pyconflict.infrastructure.repositories.pypi_repository import PyPIPackageRepository


class Container:
    """Dependency injection container.

    Builds and wires up all dependencies for the application.
    """

    def __init__(self) -> None:
        """Initialize the container."""
        self._instances = {}

    # Infrastructure Layer

    def cache_repository(self) -> DiskCacheRepository:
        """Get cache repository instance."""
        if "cache" not in self._instances:
            cache_dir = Path(user_cache_dir("pyconflict"))
            self._instances["cache"] = DiskCacheRepository(cache_dir, max_size_mb=100)
        return self._instances["cache"]

    def package_repository(self) -> PyPIPackageRepository:
        """Get package repository instance."""
        if "package_repo" not in self._instances:
            self._instances["package_repo"] = PyPIPackageRepository(
                cache=self.cache_repository(),
                base_url="https://pypi.org/pypi",
                timeout=30.0,
                max_retries=3,
            )
        return self._instances["package_repo"]

    def environment_repository(self) -> PipEnvironmentRepository:
        """Get environment repository instance."""
        if "env_repo" not in self._instances:
            self._instances["env_repo"] = PipEnvironmentRepository()
        return self._instances["env_repo"]

    # Domain Services

    def version_resolver(self) -> VersionResolver:
        """Get version resolver instance."""
        if "version_resolver" not in self._instances:
            self._instances["version_resolver"] = VersionResolver()
        return self._instances["version_resolver"]

    def conflict_detector(self) -> ConflictDetector:
        """Get conflict detector instance."""
        if "conflict_detector" not in self._instances:
            self._instances["conflict_detector"] = ConflictDetector(
                version_resolver=self.version_resolver()
            )
        return self._instances["conflict_detector"]

    def suggestion_generator(self) -> SuggestionGenerator:
        """Get suggestion generator instance."""
        if "suggestion_generator" not in self._instances:
            self._instances["suggestion_generator"] = SuggestionGenerator(
                version_resolver=self.version_resolver()
            )
        return self._instances["suggestion_generator"]

    # Use Cases

    def check_add_package_use_case(self) -> CheckAddPackageUseCase:
        """Get check-add-package use case instance."""
        return CheckAddPackageUseCase(
            package_repo=self.package_repository(),
            env_repo=self.environment_repository(),
            conflict_detector=self.conflict_detector(),
            suggestion_generator=self.suggestion_generator(),
        )

    def get_latest_stable_use_case(self) -> GetLatestStableUseCase:
        """Get get-latest-stable use case instance."""
        return GetLatestStableUseCase(package_repo=self.package_repository())


# Global container instance
_container = Container()


def get_check_add_package_use_case() -> CheckAddPackageUseCase:
    """Get the check-add-package use case."""
    return _container.check_add_package_use_case()


def get_latest_stable_use_case() -> GetLatestStableUseCase:
    """Get the get-latest-stable use case."""
    return _container.get_latest_stable_use_case()
