"""Pip-based environment repository implementation."""

import sys
from typing import Dict

try:
    # Python 3.8+
    from importlib.metadata import distributions
except ImportError:
    # Fallback for older Python
    from importlib_metadata import distributions  # type: ignore

from packaging.version import InvalidVersion, Version

from pyconflict.domain.repositories import IEnvironmentRepository


class PipEnvironmentRepository(IEnvironmentRepository):
    """Adapter for reading the current Python environment.

    Uses importlib.metadata (Python 3.8+) to read installed packages.
    """

    def get_installed_packages(self) -> Dict[str, Version]:
        """Get all installed packages.

        Returns:
            Dictionary mapping package name (lowercase) to version
        """
        packages = {}

        for dist in distributions():
            try:
                name = dist.metadata["Name"].lower()
                version = Version(dist.version)
                packages[name] = version
            except (InvalidVersion, KeyError):
                # Skip packages with invalid versions or missing names
                continue

        return packages

    def get_python_version(self) -> Version:
        """Get the current Python version.

        Returns:
            Python version
        """
        version_info = sys.version_info
        return Version(f"{version_info.major}.{version_info.minor}.{version_info.micro}")

    def get_platform(self) -> str:
        """Get the platform identifier.

        Returns:
            Platform string (e.g., 'linux', 'win32', 'darwin')
        """
        return sys.platform
