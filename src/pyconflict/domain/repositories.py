"""Repository interfaces (Ports for infrastructure adapters)."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from packaging.version import Version

from pyconflict.domain.entities import Package


class IPackageRepository(ABC):
    """Port for package metadata retrieval.

    This interface defines how the domain layer requests package information
    without knowing about PyPI, HTTP, or any external service details.
    """

    @abstractmethod
    def get_package(self, name: str, version: Optional[str] = None) -> Package:
        """Fetch package metadata.

        Args:
            name: Package name
            version: Specific version, or None for latest

        Returns:
            Package entity with metadata

        Raises:
            PackageNotFoundError: If package doesn't exist
            RepositoryError: If fetching fails
        """
        pass

    @abstractmethod
    def get_latest_stable(
        self, name: str, python_version: Optional[Version] = None
    ) -> Version:
        """Get the latest stable (non-prerelease) version.

        Args:
            name: Package name
            python_version: Filter by Python version compatibility

        Returns:
            Latest stable version

        Raises:
            PackageNotFoundError: If package doesn't exist
            RepositoryError: If fetching fails
        """
        pass

    @abstractmethod
    def get_all_versions(self, name: str) -> List[Version]:
        """Get all available versions of a package.

        Args:
            name: Package name

        Returns:
            List of all versions, sorted newest first

        Raises:
            PackageNotFoundError: If package doesn't exist
            RepositoryError: If fetching fails
        """
        pass


class ICacheRepository(ABC):
    """Port for caching.

    Provides a simple key-value cache interface.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[dict]:
        """Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value, or None if not found or expired
        """
        pass

    @abstractmethod
    def set(self, key: str, value: dict, ttl: int) -> None:
        """Store a value in cache.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time to live in seconds
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values."""
        pass


class IEnvironmentRepository(ABC):
    """Port for environment inspection.

    Provides information about the current Python environment.
    """

    @abstractmethod
    def get_installed_packages(self) -> Dict[str, Version]:
        """Get all installed packages.

        Returns:
            Dictionary mapping package name to installed version
        """
        pass

    @abstractmethod
    def get_python_version(self) -> Version:
        """Get the current Python version.

        Returns:
            Python version
        """
        pass

    @abstractmethod
    def get_platform(self) -> str:
        """Get the platform identifier.

        Returns:
            Platform string (e.g., 'linux', 'win32', 'darwin')
        """
        pass
