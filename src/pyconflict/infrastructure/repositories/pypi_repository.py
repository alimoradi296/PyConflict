"""PyPI package repository implementation."""

import time
from typing import Any, Dict, List, Optional, cast

import requests
from packaging.requirements import Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from pyconflict import __version__
from pyconflict.application.exceptions import PackageNotFoundError, RepositoryError
from pyconflict.domain.entities import Dependency, Package
from pyconflict.domain.repositories import ICacheRepository, IPackageRepository


class PyPIPackageRepository(IPackageRepository):
    """Adapter for PyPI JSON API.

    Fetches package metadata from PyPI with caching and rate limiting.
    """

    def __init__(
        self,
        cache: Optional[ICacheRepository] = None,
        base_url: str = "https://pypi.org/pypi",
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize the PyPI repository.

        Args:
            cache: Cache repository for storing responses
            base_url: PyPI API base URL
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self._cache = cache
        self._base_url = base_url
        self._timeout = timeout
        self._max_retries = max_retries
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": f"PyConflict/{__version__} (Python Dependency Checker)",
                "Accept": "application/json",
            }
        )

    def get_package(self, name: str, version: Optional[str] = None) -> Package:
        """Fetch package metadata from PyPI.

        Args:
            name: Package name
            version: Specific version, or None for latest

        Returns:
            Package entity

        Raises:
            PackageNotFoundError: If package doesn't exist
            RepositoryError: If fetching fails
        """
        # Check cache first
        cache_key = self._make_cache_key(name, version)
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached:
                return self._parse_package(cached)

        # Fetch from PyPI
        data = self._fetch_from_pypi(name, version)

        # Cache the result
        if self._cache:
            self._cache.set(cache_key, data, ttl=3600)  # 1 hour TTL

        return self._parse_package(data)

    def get_latest_stable(self, name: str, python_version: Optional[Version] = None) -> Version:
        """Get the latest stable version.

        Args:
            name: Package name
            python_version: Filter by Python version compatibility

        Returns:
            Latest stable version

        Raises:
            PackageNotFoundError: If package doesn't exist
            RepositoryError: If no stable version found
        """
        data = self._fetch_from_pypi(name, version=None)
        releases = data.get("releases", {})
        stable = []

        for version_text, files in releases.items():
            try:
                version = Version(version_text)
            except InvalidVersion:
                continue
            if version.is_prerelease or version.is_devrelease:
                continue

            if python_version is not None and not self._release_supports_python(
                files, python_version
            ):
                continue
            stable.append(version)

        if not stable:
            qualifier = f" compatible with Python {python_version}" if python_version else ""
            raise RepositoryError(f"No stable version found for {name}{qualifier}")
        return max(stable)

    @staticmethod
    def _release_supports_python(files: list, python_version: Version) -> bool:
        """Return whether at least one non-yanked release file supports Python."""
        for file_info in files:
            if file_info.get("yanked", False):
                continue
            requires_python = file_info.get("requires_python")
            if not requires_python:
                return True
            try:
                if SpecifierSet(requires_python).contains(python_version, prereleases=True):
                    return True
            except InvalidSpecifier:
                continue
        return False

    def get_all_versions(self, name: str) -> List[Version]:
        """Get all available versions.

        Args:
            name: Package name

        Returns:
            List of versions, sorted newest first

        Raises:
            PackageNotFoundError: If package doesn't exist
        """
        data = self._fetch_from_pypi(name, version=None)
        releases = data.get("releases", {})

        versions = []
        for version_str in releases.keys():
            try:
                versions.append(Version(version_str))
            except InvalidVersion:
                # Skip invalid versions
                continue

        return sorted(versions, reverse=True)

    def _fetch_from_pypi(self, name: str, version: Optional[str]) -> dict:
        """Fetch data from PyPI with retry logic.

        Args:
            name: Package name
            version: Specific version or None

        Returns:
            Raw JSON response from PyPI

        Raises:
            PackageNotFoundError: If package doesn't exist
            RepositoryError: If fetching fails
        """
        url = self._make_url(name, version)

        for attempt in range(self._max_retries):
            try:
                response = self._session.get(url, timeout=self._timeout)

                if response.status_code == 404:
                    raise PackageNotFoundError(name)

                if response.status_code == 429:
                    # Rate limited - exponential backoff
                    wait_time = 2**attempt
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise RepositoryError(f"Invalid JSON response for {name}")
                return cast(Dict[str, Any], payload)

            except requests.exceptions.Timeout as e:
                if attempt == self._max_retries - 1:
                    raise RepositoryError(f"Timeout fetching {name}: {e}") from e
                time.sleep(2**attempt)

            except requests.exceptions.RequestException as e:
                if attempt == self._max_retries - 1:
                    raise RepositoryError(f"Failed to fetch {name}: {e}") from e
                time.sleep(2**attempt)

        raise RepositoryError(f"Failed to fetch {name} after {self._max_retries} attempts")

    def _parse_package(self, data: dict) -> Package:
        """Parse PyPI JSON response into domain entity.

        Args:
            data: Raw PyPI JSON response

        Returns:
            Package entity
        """
        info = data["info"]

        dependencies = []
        if info.get("requires_dist"):
            for req_string in info["requires_dist"]:
                try:
                    dep = self._parse_requirement(req_string)
                    dependencies.append(dep)
                except Exception:
                    # Skip invalid requirements
                    continue

        return Package(
            name=info["name"],
            version=Version(info["version"]),
            requires_python=info.get("requires_python"),
            dependencies=dependencies,
        )

    def _parse_requirement(self, req_string: str) -> Dependency:
        """Parse PEP 508 requirement string.

        Args:
            req_string: Requirement string (e.g., "requests>=2.28.0")

        Returns:
            Dependency entity
        """
        req = Requirement(req_string)

        return Dependency(
            name=req.name,
            specifier=req.specifier if req.specifier else SpecifierSet(""),
            markers=str(req.marker) if req.marker else None,
            extras=set(req.extras),
        )

    def _make_url(self, name: str, version: Optional[str]) -> str:
        """Construct PyPI API URL.

        Args:
            name: Package name
            version: Version or None

        Returns:
            Full URL
        """
        if version:
            return f"{self._base_url}/{name}/{version}/json"
        return f"{self._base_url}/{name}/json"

    def _make_cache_key(self, name: str, version: Optional[str]) -> str:
        """Generate cache key.

        Args:
            name: Package name
            version: Version or None

        Returns:
            Cache key
        """
        if version:
            return f"package:{name}:{version}"
        return f"package:{name}:latest"
