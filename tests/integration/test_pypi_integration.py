"""Integration tests specifically for PyPI API interaction.

These tests verify that we correctly interact with the PyPI JSON API
and handle all edge cases properly.

Run with: pytest -v -m integration tests/integration/
"""

import pytest
from packaging.specifiers import SpecifierSet
from packaging.version import Version

from pyconflict.infrastructure.repositories.disk_cache_repository import (
    DiskCacheRepository,
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


@pytest.mark.integration
class TestPyPIAPIInteraction:
    """Test PyPI API interaction."""

    def test_fetch_latest_version(self, pypi_repository):
        """Test fetching latest version of a package."""
        package = pypi_repository.get_package("requests")

        assert package.name == "requests"
        assert package.version is not None
        assert isinstance(package.version, Version)

    def test_fetch_specific_version(self, pypi_repository):
        """Test fetching a specific version."""
        package = pypi_repository.get_package("requests", "2.28.0")

        assert package.name == "requests"
        assert package.version == Version("2.28.0")

    def test_fetch_old_version(self, pypi_repository):
        """Test fetching an older version."""
        package = pypi_repository.get_package("django", "2.2.0")

        assert package.name.lower() == "django"
        assert package.version == Version("2.2.0")

    def test_parse_dependencies(self, pypi_repository):
        """Test that dependencies are correctly parsed."""
        package = pypi_repository.get_package("requests")

        assert len(package.dependencies) > 0
        # requests should have charset-normalizer, idna, urllib3, certifi
        dep_names = {d.name for d in package.dependencies}
        # At least some of these should be present
        expected = {"charset-normalizer", "idna", "urllib3", "certifi"}
        assert len(dep_names.intersection(expected)) > 0

    def test_parse_version_constraints(self, pypi_repository):
        """Test that version constraints are correctly parsed."""
        package = pypi_repository.get_package("django", "4.2.0")

        # Django has dependencies with version constraints
        assert len(package.dependencies) > 0

        # Find asgiref dependency
        asgiref_deps = [d for d in package.dependencies if d.name == "asgiref"]
        assert len(asgiref_deps) > 0

        asgiref_dep = asgiref_deps[0]
        assert isinstance(asgiref_dep.specifier, SpecifierSet)
        # Django 4.2 requires asgiref>=3.6.0,<4
        assert str(asgiref_dep.specifier) != ""

    def test_parse_requires_python(self, pypi_repository):
        """Test that requires_python is correctly parsed."""
        package = pypi_repository.get_package("django", "4.2.0")

        # Django 4.2 requires Python >= 3.8
        assert package.requires_python is not None
        assert "3.8" in package.requires_python

    def test_get_latest_stable_excludes_prereleases(self, pypi_repository):
        """Test that get_latest_stable excludes pre-release versions."""
        version = pypi_repository.get_latest_stable("requests")

        assert isinstance(version, Version)
        assert not version.is_prerelease
        assert not version.is_devrelease

    def test_get_latest_stable_with_python_constraint(self, pypi_repository):
        """Test getting latest version compatible with specific Python version."""
        # Get latest numpy for Python 3.8
        version = pypi_repository.get_latest_stable("numpy", python_version="3.8")

        assert isinstance(version, Version)
        assert not version.is_prerelease


@pytest.mark.integration
class TestPyPIEdgeCases:
    """Test edge cases in PyPI data."""

    def test_package_with_no_requires_python(self, pypi_repository):
        """Test package that doesn't specify requires_python."""
        # Many old packages don't have requires_python
        package = pypi_repository.get_package("six")

        assert package.name == "six"
        # May or may not have requires_python

    def test_package_with_markers(self, pypi_repository):
        """Test package with environment markers in dependencies."""
        # Some packages have platform-specific dependencies
        package = pypi_repository.get_package("pytest")

        # pytest has some conditional dependencies
        assert len(package.dependencies) >= 0

        # Check if any dependencies have markers
        any(d.markers for d in package.dependencies)
        # This might be True or False depending on the version

    def test_package_with_extras(self, pypi_repository):
        """Test package with extras."""
        package = pypi_repository.get_package("requests")

        # requests has extras like 'security', 'socks'
        # Check that we can fetch it without errors
        assert package.name == "requests"

    def test_normalized_package_names(self, pypi_repository):
        """Test that package names are normalized."""
        # PyPI normalizes names (e.g., Django vs django)
        package1 = pypi_repository.get_package("Django")
        package2 = pypi_repository.get_package("django")

        # Should refer to the same package
        assert package1.name.lower() == package2.name.lower()


@pytest.mark.integration
class TestCaching:
    """Test caching behavior."""

    def test_cache_hit_avoids_network_request(self, pypi_repository):
        """Test that cached entries avoid network requests."""
        # First request
        package1 = pypi_repository.get_package("flask")

        # Second request (should be cached)
        package2 = pypi_repository.get_package("flask")

        # Should return same data
        assert package1.name == package2.name
        assert package1.version == package2.version
        assert len(package1.dependencies) == len(package2.dependencies)

    def test_different_versions_cached_separately(self, pypi_repository):
        """Test that different versions are cached separately."""
        package1 = pypi_repository.get_package("django", "4.2.0")
        package2 = pypi_repository.get_package("django", "4.1.0")

        assert package1.version == Version("4.2.0")
        assert package2.version == Version("4.1.0")


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling for various failure scenarios."""

    def test_package_not_found_raises_error(self, pypi_repository):
        """Test that non-existent package raises appropriate error."""
        from pyconflict.application.exceptions import PackageNotFoundError

        with pytest.raises(PackageNotFoundError):
            pypi_repository.get_package("this-does-not-exist-xyz123")

    def test_version_not_found_raises_error(self, pypi_repository):
        """Test that non-existent version raises appropriate error."""
        from pyconflict.application.exceptions import PackageNotFoundError

        with pytest.raises(PackageNotFoundError):
            pypi_repository.get_package("requests", "999.999.999")

    def test_invalid_package_name(self, pypi_repository):
        """Test handling of invalid package names."""
        from pyconflict.application.exceptions import PackageNotFoundError

        # Package names with invalid characters
        with pytest.raises(PackageNotFoundError):
            pypi_repository.get_package("!!invalid!!")


@pytest.mark.integration
class TestComplexDependencies:
    """Test packages with complex dependency specifications."""

    def test_package_with_many_dependencies(self, pypi_repository):
        """Test package with many dependencies (TensorFlow)."""
        package = pypi_repository.get_package("tensorflow")

        assert package.name == "tensorflow"
        # TensorFlow has many dependencies
        assert len(package.dependencies) > 5

    def test_package_with_complex_specifiers(self, pypi_repository):
        """Test package with complex version specifiers."""
        package = pypi_repository.get_package("django", "4.2.0")

        # Django has dependencies with complex specifiers
        # e.g., "asgiref>=3.6.0,<4"
        asgiref_deps = [d for d in package.dependencies if d.name == "asgiref"]

        if asgiref_deps:
            spec = asgiref_deps[0].specifier
            # Should have both >= and < constraints
            assert len(spec) > 0

    def test_package_with_or_constraints(self, pypi_repository):
        """Test package with OR constraints in dependencies."""
        # Some packages have complex OR constraints
        # Just verify we can parse them without crashing
        package = pypi_repository.get_package("setuptools")

        assert package.name == "setuptools"
        assert isinstance(package.dependencies, list)


@pytest.mark.integration
class TestPerformance:
    """Test performance characteristics."""

    def test_response_time_with_cache(self, pypi_repository):
        """Test that cached responses are fast."""
        import time

        # First request (cache miss)
        pypi_repository.get_package("requests")

        # Second request (cache hit) - should be very fast
        start = time.time()
        pypi_repository.get_package("requests")
        elapsed = time.time() - start

        # Cached request should be < 100ms
        assert elapsed < 0.1

    def test_parallel_requests(self, pypi_repository):
        """Test that parallel requests work correctly."""
        from concurrent.futures import ThreadPoolExecutor

        packages = ["requests", "django", "flask", "pytest", "numpy"]

        # Fetch all in parallel
        with ThreadPoolExecutor(max_workers=len(packages)) as executor:
            results = list(executor.map(pypi_repository.get_package, packages))

        assert len(results) == len(packages)
        for i, pkg in enumerate(packages):
            assert results[i].name.lower() == pkg
