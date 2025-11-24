"""Application-level exceptions."""


class ApplicationException(Exception):
    """Base exception for application errors."""

    pass


class PackageNotFoundError(ApplicationException):
    """Package not found in repository."""

    def __init__(self, package_name: str, message: str = "") -> None:
        self.package_name = package_name
        super().__init__(message or f"Package not found: {package_name}")


class EnvironmentError(ApplicationException):
    """Cannot read environment."""

    pass


class RepositoryError(ApplicationException):
    """Repository operation failed."""

    pass
