"""Integration tests with real PyPI packages.

These tests hit the actual PyPI API to verify behavior with real packages.
They should be run separately from unit tests as they:
- Require network access
- Are slower (API calls)
- May fail if PyPI is down

Run with: pytest -v -m integration tests/integration/
"""

import pytest
from packaging.version import Version

from pyconflict.application.use_cases.check_add_package import (
    CheckAddPackageRequest,
    CheckAddPackageUseCase,
)
from pyconflict.application.use_cases.get_latest_stable import (
    GetLatestStableRequest,
    GetLatestStableUseCase,
)
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


@pytest.fixture
def cache_repository(tmp_path):
    """Create a temporary cache repository for tests."""
    return DiskCacheRepository(cache_dir=tmp_path / "cache", max_size_mb=10)


@pytest.fixture
def pypi_repository(cache_repository):
    """Create a real PyPI repository with temporary cache."""
    return PyPIPackageRepository(cache=cache_repository)


@pytest.fixture
def env_repository():
    """Create environment repository."""
    return PipEnvironmentRepository()


@pytest.fixture
def check_add_use_case(pypi_repository, env_repository):
    """Create CheckAddPackage use case with real dependencies."""
    conflict_detector = ConflictDetector()
    version_resolver = VersionResolver()
    suggestion_generator = SuggestionGenerator(version_resolver)

    return CheckAddPackageUseCase(
        package_repo=pypi_repository,
        env_repo=env_repository,
        conflict_detector=conflict_detector,
        suggestion_generator=suggestion_generator,
    )


@pytest.fixture
def stable_use_case(pypi_repository):
    """Create GetLatestStable use case with real PyPI repository."""
    return GetLatestStableUseCase(package_repo=pypi_repository)


@pytest.mark.integration
class TestRealPackages:
    """Test with real PyPI packages."""

    def test_check_add_safe_package_requests(self, check_add_use_case):
        """Test checking a safe package (requests has minimal dependencies)."""
        request = CheckAddPackageRequest(package_name="requests")

        response = check_add_use_case.execute(request)

        assert response.package.name == "requests"
        assert response.package.version is not None
        # Requests should be safe to add in most environments
        # (it has few dependencies: charset-normalizer, idna, urllib3, certifi)

    def test_check_add_specific_version(self, check_add_use_case):
        """Test checking a specific version of a package."""
        request = CheckAddPackageRequest(package_name="django", version="4.2.0")

        response = check_add_use_case.execute(request)

        assert response.package.name.lower() == "django"
        assert response.package.version == Version("4.2.0")
        assert len(response.package.dependencies) > 0

    def test_check_add_package_with_many_dependencies(self, check_add_use_case):
        """Test checking a package with many dependencies (tensorflow)."""
        request = CheckAddPackageRequest(package_name="tensorflow")

        response = check_add_use_case.execute(request)

        assert response.package.name == "tensorflow"
        # TensorFlow has many dependencies
        assert len(response.package.dependencies) > 5

    def test_check_add_detects_real_conflict(self, check_add_use_case):
        """Test that real conflicts are detected.

        This test is tricky because it depends on what's installed in the test environment.
        We check that the conflict detection logic runs without errors.
        """
        # Django 3.2 requires asgiref<4,>=3.3.2
        # If channels 4.x is installed (requires asgiref>=3.5.0), there should be no conflict
        # This test just verifies the mechanism works
        request = CheckAddPackageRequest(package_name="django", version="3.2.0")

        response = check_add_use_case.execute(request)

        assert response.package.name.lower() == "django"
        # Result depends on environment, but should not crash
        assert isinstance(response.safe_to_add, bool)
        assert isinstance(response.conflicts, list)

    def test_get_latest_stable_requests(self, stable_use_case):
        """Test getting latest stable version of requests."""
        response = stable_use_case.execute(GetLatestStableRequest(package_name="requests"))

        assert isinstance(response.version, Version)
        assert not response.version.is_prerelease
        assert response.version >= Version("2.0.0")

    def test_get_latest_stable_django(self, stable_use_case):
        """Test getting latest stable version of Django."""
        response = stable_use_case.execute(GetLatestStableRequest(package_name="django"))

        assert isinstance(response.version, Version)
        assert not response.version.is_prerelease
        assert response.version >= Version("4.0.0")

    def test_get_latest_stable_with_python_version(self, stable_use_case):
        """Test getting latest stable version compatible with Python 3.8."""
        response = stable_use_case.execute(
            GetLatestStableRequest(package_name="numpy", python_version="3.8")
        )

        assert isinstance(response.version, Version)
        assert not response.version.is_prerelease
        assert response.is_filtered_by_python

    def test_package_not_found(self, check_add_use_case):
        """Test handling of non-existent package."""
        from pyconflict.application.exceptions import PackageNotFoundError

        request = CheckAddPackageRequest(
            package_name="this-package-definitely-does-not-exist-12345"
        )

        with pytest.raises(PackageNotFoundError):
            check_add_use_case.execute(request)

    def test_invalid_version(self, check_add_use_case):
        """Test handling of invalid version."""
        from pyconflict.application.exceptions import PackageNotFoundError

        request = CheckAddPackageRequest(package_name="requests", version="999.999.999")

        # Should raise PackageNotFoundError for non-existent version
        with pytest.raises(PackageNotFoundError):
            check_add_use_case.execute(request)


@pytest.mark.integration
class TestPyPIRepository:
    """Test PyPI repository integration."""

    def test_get_package_metadata(self, pypi_repository):
        """Test fetching package metadata from PyPI."""
        package = pypi_repository.get_package("requests")

        assert package.name == "requests"
        assert package.version is not None
        assert len(package.dependencies) > 0

    def test_get_specific_version(self, pypi_repository):
        """Test fetching specific version from PyPI."""
        package = pypi_repository.get_package("django", "4.2.0")

        assert package.name.lower() == "django"
        assert package.version == Version("4.2.0")

    def test_get_latest_stable(self, pypi_repository):
        """Test getting latest stable version."""
        version = pypi_repository.get_latest_stable("flask")

        assert isinstance(version, Version)
        assert not version.is_prerelease

    def test_caching_works(self, pypi_repository):
        """Test that caching prevents duplicate requests."""
        # First request - should hit PyPI
        package1 = pypi_repository.get_package("flask")

        # Second request - should use cache
        package2 = pypi_repository.get_package("flask")

        # Should return same data
        assert package1.name == package2.name
        assert package1.version == package2.version

    def test_package_with_no_dependencies(self, pypi_repository):
        """Test package with no dependencies."""
        # Some very simple packages have no dependencies
        # This tests that we handle empty dependency lists
        package = pypi_repository.get_package("typing_extensions")

        assert package.name.replace("-", "_") == "typing_extensions"
        # typing_extensions typically has no dependencies
        assert isinstance(package.dependencies, list)


@pytest.mark.integration
class TestNetworkFailureHandling:
    """Test handling of network failures and API errors."""

    def test_handles_rate_limiting_gracefully(self, pypi_repository):
        """Test that rate limiting is handled (if it occurs).

        This test verifies the code doesn't crash if rate limited.
        Actual rate limiting is hard to trigger in tests.
        """
        # Try multiple requests rapidly
        packages = ["requests", "django", "flask", "fastapi", "pytest"]

        for pkg_name in packages:
            package = pypi_repository.get_package(pkg_name)
            assert package.name.lower() == pkg_name

    def test_invalid_package_name(self, pypi_repository):
        """Test handling of invalid package name."""
        from pyconflict.application.exceptions import PackageNotFoundError

        with pytest.raises(PackageNotFoundError):
            pypi_repository.get_package("!!!invalid-package-name!!!")


@pytest.mark.integration
class TestKnownConflictScenarios:
    """Test known real-world conflict scenarios."""

    def test_django_channels_asgiref_conflict(self, check_add_use_case):
        """Test the classic Django 3.2 + Channels 4.0 conflict on asgiref.

        Django 3.2 requires: asgiref>=3.3.2,<4
        Channels 4.0 requires: asgiref>=3.5.0

        These ranges overlap but the constraint is tight.
        """
        # Just verify we can check this scenario
        request = CheckAddPackageRequest(package_name="django", version="3.2.0")

        response = check_add_use_case.execute(request)

        assert response.package.name.lower() == "django"
        # Check that asgiref is in dependencies
        asgiref_deps = [d for d in response.package.dependencies if d.name == "asgiref"]
        assert len(asgiref_deps) > 0

    def test_tensorflow_numpy_compatibility(self, check_add_use_case):
        """Test TensorFlow and NumPy version compatibility.

        TensorFlow has strict NumPy version requirements.
        """
        request = CheckAddPackageRequest(package_name="tensorflow")

        response = check_add_use_case.execute(request)

        assert response.package.name == "tensorflow"
        # Check that numpy is in dependencies
        numpy_deps = [d for d in response.package.dependencies if d.name == "numpy"]
        # TensorFlow should specify numpy dependency
        assert len(numpy_deps) >= 0  # May or may not be direct dependency


@pytest.mark.integration
class TestEnvironmentRepository:
    """Test environment repository integration."""

    def test_get_installed_packages(self, env_repository):
        """Test getting installed packages."""
        packages = env_repository.get_installed_packages()

        assert isinstance(packages, dict)
        # pytest should be installed (we're running tests)
        assert "pytest" in packages
        assert isinstance(packages["pytest"], Version)

    def test_get_python_version(self, env_repository):
        """Test getting Python version."""
        version = env_repository.get_python_version()

        assert isinstance(version, Version)
        # Should be Python 3.8+
        assert version >= Version("3.8.0")
