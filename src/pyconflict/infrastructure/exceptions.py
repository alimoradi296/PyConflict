"""Infrastructure-level exceptions."""


class InfrastructureException(Exception):
    """Base exception for infrastructure errors."""

    pass


class PyPIAPIError(InfrastructureException):
    """PyPI API returned error."""

    pass


class CacheError(InfrastructureException):
    """Cache operation failed."""

    pass


class RateLimitError(InfrastructureException):
    """Rate limit exceeded."""

    pass
