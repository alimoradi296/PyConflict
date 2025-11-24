"""Domain-level exceptions."""


class DomainException(Exception):
    """Base exception for domain errors."""

    pass


class InvalidVersionError(DomainException):
    """Invalid version string."""

    def __init__(self, version: str, message: str = "") -> None:
        self.version = version
        super().__init__(message or f"Invalid version: {version}")


class IncompatibleConstraintError(DomainException):
    """Constraint cannot be satisfied."""

    def __init__(self, constraint: str, message: str = "") -> None:
        self.constraint = constraint
        super().__init__(message or f"Incompatible constraint: {constraint}")
