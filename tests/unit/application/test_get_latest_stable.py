"""Tests for GetLatestStableUseCase."""

from typing import Dict, List, Optional

from packaging.version import Version

from pyconflict.application.use_cases.get_latest_stable import (
    GetLatestStableRequest,
    GetLatestStableUseCase,
)
from pyconflict.domain.entities import Package
from pyconflict.domain.repositories import IPackageRepository


class MockPackageRepository(IPackageRepository):
    """Mock package repository for testing."""

    def __init__(self) -> None:
        self._packages: Dict[str, Package] = {}
        self._versions: Dict[str, List[Version]] = {}

    def add_package(self, name: str, package: Package) -> None:
        """Add a package to the mock repository."""
        self._packages[name.lower()] = package

    def set_versions(self, name: str, versions: List[Version]) -> None:
        """Set available versions for a package."""
        self._versions[name.lower()] = versions

    def get_package(self, name: str, version: Optional[str] = None) -> Package:
        """Get package from mock repository."""
        package = self._packages.get(name.lower())
        if not package:
            from pyconflict.application.exceptions import PackageNotFoundError

            raise PackageNotFoundError(name)
        return package

    def get_latest_stable(
        self, name: str, python_version: Optional[Version] = None
    ) -> Version:
        """Get latest stable version."""
        versions = self._versions.get(name.lower(), [])
        if not versions:
            from pyconflict.application.exceptions import RepositoryError

            raise RepositoryError(f"No versions found for {name}")

        # Filter out prereleases
        stable = [v for v in versions if not v.is_prerelease]

        if not stable:
            from pyconflict.application.exceptions import RepositoryError

            raise RepositoryError(f"No stable version found for {name}")

        return max(stable)

    def get_all_versions(self, name: str) -> List[Version]:
        """Get all versions."""
        return self._versions.get(name.lower(), [])


def test_get_latest_stable_basic():
    """Test getting latest stable version."""
    # Setup
    package_repo = MockPackageRepository()
    package_repo.set_versions(
        "pandas",
        [
            Version("1.0.0"),
            Version("1.5.0"),
            Version("2.0.0"),
            Version("2.1.4"),
        ],
    )

    # Create use case
    use_case = GetLatestStableUseCase(package_repo=package_repo)

    # Execute
    request = GetLatestStableRequest(package_name="pandas")
    response = use_case.execute(request)

    # Assert
    assert response.package_name == "pandas"
    assert response.version == Version("2.1.4")
    assert response.is_filtered_by_python is False


def test_get_latest_stable_filters_prereleases():
    """Test that prereleases are filtered out."""
    # Setup
    package_repo = MockPackageRepository()
    package_repo.set_versions(
        "numpy",
        [
            Version("1.24.0"),
            Version("1.25.0rc1"),
            Version("1.25.0a1"),
            Version("1.25.0b2"),
            Version("1.24.4"),
        ],
    )

    # Create use case
    use_case = GetLatestStableUseCase(package_repo=package_repo)

    # Execute
    request = GetLatestStableRequest(package_name="numpy")
    response = use_case.execute(request)

    # Assert - should return 1.24.4, not the RC/alpha/beta
    assert response.version == Version("1.24.4")


def test_get_latest_stable_with_python_version():
    """Test getting latest stable with Python version filter."""
    # Setup
    package_repo = MockPackageRepository()
    package_repo.set_versions(
        "numpy",
        [
            Version("1.20.0"),
            Version("1.24.0"),
        ],
    )

    # Create use case
    use_case = GetLatestStableUseCase(package_repo=package_repo)

    # Execute with Python version
    request = GetLatestStableRequest(package_name="numpy", python_version="3.8")
    response = use_case.execute(request)

    # Assert
    assert response.package_name == "numpy"
    assert response.is_filtered_by_python is True
    # Note: In MVP, we don't actually filter by Python version yet
    # This test documents the intended behavior for Phase 2


def test_get_latest_stable_package_not_found():
    """Test getting latest stable for non-existent package."""
    # Setup
    package_repo = MockPackageRepository()

    # Create use case
    use_case = GetLatestStableUseCase(package_repo=package_repo)

    # Execute and expect exception
    request = GetLatestStableRequest(package_name="nonexistent")

    try:
        response = use_case.execute(request)
        assert False, "Should have raised RepositoryError"
    except Exception as e:
        from pyconflict.application.exceptions import RepositoryError

        assert isinstance(e, RepositoryError)
