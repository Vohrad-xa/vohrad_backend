"""Infrastructure layer exceptions for external dependencies."""

from .base import BaseAppException
from fastapi import status
from typing import Any
from typing import Dict
from typing import Optional


class InfrastructureException(BaseAppException):
    """Base class for infrastructure layer exceptions."""

    def __init__(
        self,
    message    : str,
    error_code : str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details    : Optional[Dict[str, Any]] = None,
    )          :
        super().__init__(message, error_code, status_code, details)


class DatabaseException(InfrastructureException):
    """Database-related exceptions."""

    def __init__(self, message: str, operation: str, details: Optional[Dict[str, Any]] = None):
        error_details = {"operation": operation}
        if details:
            error_details.update(details)

        super().__init__(
            message     = f"Database error during {operation}: {message}",
            error_code  = "DATABASE_ERROR",
            details     = error_details,
        )


class DatabaseConnectionException(InfrastructureException):
    """Database connection failures."""

    def __init__(self, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message     = "Unable to establish database connection",
            error_code  = "DATABASE_CONNECTION_FAILED",
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
            details     = details,
        )


class ExternalServiceException(InfrastructureException):
    """External service communication failures."""

    def __init__(self, service_name: str, operation: str, details: Optional[Dict[str, Any]] = None):
        error_details = {"service": service_name, "operation": operation}
        if details:
            error_details.update(details)

        super().__init__(
            message     = f"External service '{service_name}' failed during {operation}",
            error_code  = "EXTERNAL_SERVICE_ERROR",
            status_code = status.HTTP_502_BAD_GATEWAY,
            details     = error_details,
        )


class CacheException(InfrastructureException):
    """Cache-related exceptions."""

    def __init__(self, operation: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message    = f"Cache error during {operation}",
            error_code = "CACHE_ERROR",
            details    = {"operation": operation, **(details or {})},
        )


class FileSystemException(InfrastructureException):
    """File system operation exceptions."""

    def __init__(self, operation: str, path: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message    = f"File system error during {operation} at {path}",
            error_code = "FILESYSTEM_ERROR",
            details    = {"operation": operation, "path": path, **(details or {})},
        )


class NetworkException(InfrastructureException):
    """Network-related exceptions."""

    def __init__(self, operation: str, endpoint: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message     = f"Network error during {operation} to {endpoint}",
            error_code  = "NETWORK_ERROR",
            status_code = status.HTTP_502_BAD_GATEWAY,
            details     = {"operation": operation, "endpoint": endpoint, **(details or {})},
        )
