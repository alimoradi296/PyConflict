"""Tests for CheckAddPackageUseCase."""

from typing import Dict, List, Optional

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from pyconflict.application.use_cases.check_add_package import (
    CheckAddPackageRequest,
    CheckAddPackageUseCase,
)
from pyconflict.domain.entities import Dependency, Environment, Package
from pyconflict.domain.repositories import IEnvironmentRepository, IPackageRepository
from pyconflict.domain.services.conflict_detector import ConflictDetector
from pyconflict.domain.services.suggestion_generator import SuggestionGenerator
from pyconflict.domain.services.version_resolver import VersionResolver


# Mock Repositories
class MockPackageRepository(IPackageRepository):
    """Mock package repository for testing."""

    def __init__(self) -> None:
        self._packages: Dict[str, Package] = {}

    def add_package(self, name: str, package: Package) -> None:
        """Add a package to the mock repository."""
        self._packages[name.lower()] = package

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
        package = self.get_package(name)
        return package.version

    def get_all_versions(self, name: str) -> List[Version]:
        """Get all versions."""
        package = self.get_package(name)
        return [package.version]


class MockEnvironmentRepository(IEnvironmentRepository):
    """Mock environment repository for testing."""

    def __init__(self) -> None:
        self._packages: Dict[str, Version] = {}
        self._python_version = Version("3.11.0")
        self._platform = "linux"

    def set_installed(self, packages: Dict[str, Version]) -> None:
        """Set installed packages."""
        self._packages = packages

    def get_installed_packages(self) -> Dict[str, Version]:
        """Get installed packages."""
        return self._packages

    def get_python_version(self) -> Version:
        """Get Python version."""
        return self._python_version

    def get_platform(self) -> str:
        """Get platform."""
        return self._platform


# Tests
def test_check_add_package_no_conflicts():
    """Test checking a package with no conflicts."""
    # Setup
    package_repo = MockPackageRepository()
    env_repo = MockEnvironmentRepository()

    # Add a package with dependencies that don't conflict
    package = Package(
        name="requests",
        version=Version("2.31.0"),
        dependencies=[
            Dependency(
                name="urllib3",
                specifier=SpecifierSet(">=1.21.1,<3"),
            ),
            Dependency(
                name="certifi",
                specifier=SpecifierSet(">=2017.4.17"),
            ),
        ],
    )
    package_repo.add_package("requests", package)

    # Environment has compatible versions
    env_repo.set_installed(
        {
            "urllib3": Version("2.0.0"),
            "certifi": Version("2023.7.22"),
        }
    )

    # Create use case
    use_case = CheckAddPackageUseCase(
        package_repo=package_repo,
        env_repo=env_repo,
        conflict_detector=ConflictDetector(VersionResolver()),
        suggestion_generator=SuggestionGenerator(VersionResolver()),
    )

    # Execute
    request = CheckAddPackageRequest(package_name="requests")
    response = use_case.execute(request)

    # Assert
    assert response.safe_to_add is True
    assert len(response.conflicts) == 0
    assert response.package.name == "requests"
    assert response.confidence > 0.8


def test_check_add_package_with_conflict():
    """Test checking a package that has conflicts."""
    # Setup
    package_repo = MockPackageRepository()
    env_repo = MockEnvironmentRepository()

    # Add Django 3.2 which requires asgiref>=3.3.2,<4
    package = Package(
        name="django",
        version=Version("3.2.0"),
        dependencies=[
            Dependency(
                name="asgiref",
                specifier=SpecifierSet(">=3.3.2,<4"),
            ),
        ],
    )
    package_repo.add_package("django", package)

    # Environment has asgiref 4.0.0 (incompatible with django 3.2)
    env_repo.set_installed(
        {
            "asgiref": Version("4.0.0"),
        }
    )

    # Create use case
    use_case = CheckAddPackageUseCase(
        package_repo=package_repo,
        env_repo=env_repo,
        conflict_detector=ConflictDetector(VersionResolver()),
        suggestion_generator=SuggestionGenerator(VersionResolver()),
    )

    # Execute
    request = CheckAddPackageRequest(package_name="django", version="3.2.0")
    response = use_case.execute(request)

    # Assert
    assert response.safe_to_add is False
    assert len(response.conflicts) == 1
    assert response.conflicts[0].dependency_name == "asgiref"
    assert len(response.suggestions) > 0


def test_check_add_package_with_uninstalled_dependency():
    """Test checking a package when dependency is not installed."""
    # Setup
    package_repo = MockPackageRepository()
    env_repo = MockEnvironmentRepository()

    # Add a package with a dependency
    package = Package(
        name="requests",
        version=Version("2.31.0"),
        dependencies=[
            Dependency(
                name="urllib3",
                specifier=SpecifierSet(">=1.21.1,<3"),
            ),
        ],
    )
    package_repo.add_package("requests", package)

    # Environment is empty (no packages installed)
    env_repo.set_installed({})

    # Create use case
    use_case = CheckAddPackageUseCase(
        package_repo=package_repo,
        env_repo=env_repo,
        conflict_detector=ConflictDetector(VersionResolver()),
        suggestion_generator=SuggestionGenerator(VersionResolver()),
    )

    # Execute
    request = CheckAddPackageRequest(package_name="requests")
    response = use_case.execute(request)

    # Assert - no conflict because dependency will be installed
    assert response.safe_to_add is True
    assert len(response.conflicts) == 0


def test_check_add_package_not_found():
    """Test checking a package that doesn't exist."""
    # Setup
    package_repo = MockPackageRepository()
    env_repo = MockEnvironmentRepository()

    # Create use case
    use_case = CheckAddPackageUseCase(
        package_repo=package_repo,
        env_repo=env_repo,
        conflict_detector=ConflictDetector(VersionResolver()),
        suggestion_generator=SuggestionGenerator(VersionResolver()),
    )

    # Execute and expect exception
    request = CheckAddPackageRequest(package_name="nonexistent-package")

    try:
        response = use_case.execute(request)
        assert False, "Should have raised PackageNotFoundError"
    except Exception as e:
        from pyconflict.application.exceptions import PackageNotFoundError

        assert isinstance(e, PackageNotFoundError)
        assert "nonexistent-package" in str(e)


def test_check_add_package_caveats():
    """Test that caveats are included in response."""
    # Setup
    package_repo = MockPackageRepository()
    env_repo = MockEnvironmentRepository()

    package = Package(
        name="requests",
        version=Version("2.31.0"),
        dependencies=[],
    )
    package_repo.add_package("requests", package)
    env_repo.set_installed({})

    # Create use case
    use_case = CheckAddPackageUseCase(
        package_repo=package_repo,
        env_repo=env_repo,
        conflict_detector=ConflictDetector(VersionResolver()),
        suggestion_generator=SuggestionGenerator(VersionResolver()),
    )

    # Execute
    request = CheckAddPackageRequest(package_name="requests", check_deep=False)
    response = use_case.execute(request)

    # Assert
    assert len(response.caveats) > 0
    assert any("direct dependencies" in caveat.lower() for caveat in response.caveats)
    assert any("platform" in caveat.lower() for caveat in response.caveats)


def test_check_add_package_multiple_conflicts():
    """Test checking a package with multiple dependency conflicts."""
    # Setup
    package_repo = MockPackageRepository()
    env_repo = MockEnvironmentRepository()

    # Add a package with multiple dependencies
    package = Package(
        name="example",
        version=Version("1.0.0"),
        dependencies=[
            Dependency(name="dep1", specifier=SpecifierSet(">=2.0,<3.0")),
            Dependency(name="dep2", specifier=SpecifierSet(">=1.5,<2.0")),
            Dependency(name="dep3", specifier=SpecifierSet(">=3.0")),
        ],
    )
    package_repo.add_package("example", package)

    # Environment has incompatible versions
    env_repo.set_installed(
        {
            "dep1": Version("1.5.0"),  # Too old
            "dep2": Version("2.5.0"),  # Too new
            "dep3": Version("2.0.0"),  # Too old
        }
    )

    # Create use case
    use_case = CheckAddPackageUseCase(
        package_repo=package_repo,
        env_repo=env_repo,
        conflict_detector=ConflictDetector(VersionResolver()),
        suggestion_generator=SuggestionGenerator(VersionResolver()),
    )

    # Execute
    request = CheckAddPackageRequest(package_name="example")
    response = use_case.execute(request)

    # Assert
    assert response.safe_to_add is False
    assert len(response.conflicts) == 3
    conflict_names = {c.dependency_name for c in response.conflicts}
    assert conflict_names == {"dep1", "dep2", "dep3"}
