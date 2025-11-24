"""Use case for getting the latest stable version of a package."""

from dataclasses import dataclass
from typing import Optional

from packaging.version import Version

from pyconflict.domain.repositories import IPackageRepository


@dataclass
class GetLatestStableRequest:
    """Request to get latest stable version."""

    package_name: str
    python_version: Optional[str] = None  # e.g., "3.8"


@dataclass
class GetLatestStableResponse:
    """Response with latest stable version."""

    package_name: str
    version: Version
    is_filtered_by_python: bool


class GetLatestStableUseCase:
    """Use case: Get the latest stable version of a package.

    Returns the latest non-prerelease version, optionally filtered
    by Python version compatibility.
    """

    def __init__(self, package_repo: IPackageRepository) -> None:
        """Initialize the use case.

        Args:
            package_repo: Repository for fetching package metadata
        """
        self._package_repo = package_repo

    def execute(self, request: GetLatestStableRequest) -> GetLatestStableResponse:
        """Execute the use case.

        Args:
            request: The request parameters

        Returns:
            Response with latest stable version
        """
        python_version = None
        if request.python_version:
            python_version = Version(request.python_version)

        version = self._package_repo.get_latest_stable(
            request.package_name, python_version
        )

        return GetLatestStableResponse(
            package_name=request.package_name,
            version=version,
            is_filtered_by_python=python_version is not None,
        )
