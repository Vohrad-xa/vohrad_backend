"""Application layer exceptions for use cases."""

from .base import BaseAppException
from fastapi import status
from typing import Any
from typing import Dict
from typing import Optional


class ApplicationException(BaseAppException):
    """Base class for application layer exceptions."""

    def __init__(
        self,
    message    : str,
    error_code : str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details    : Optional[Dict[str, Any]] = None,
    )          :
        super().__init__(message, error_code, status_code, details)


class ValidationException(ApplicationException):
    """Input validation failures."""

    def __init__(self, field: str, message: str, details: Optional[Dict[str, Any]] = None):
        error_details = {"field": field}
        if details:
            error_details.update(details)

        super().__init__(
            message     = f"Validation error for field '{field}': {message}",
            error_code  = "VALIDATION_ERROR",
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            details     = error_details,
        )


class AuthorizationException(ApplicationException):
    """Authorization failures."""

    def __init__(self, resource: str, action: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message     = f"Not authorized to {action} {resource}",
            error_code  = "AUTHORIZATION_FAILED",
            status_code = status.HTTP_403_FORBIDDEN,
            details     = {"resource": resource, "action": action, **(details or {})},
        )


class AuthenticationException(ApplicationException):
    """Authentication failures."""

    def __init__(self, reason: str = "Invalid or missing authentication", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message     = reason,
            error_code  = "AUTHENTICATION_FAILED",
            status_code = status.HTTP_401_UNAUTHORIZED,
            details     = details,
        )


class RateLimitExceededException(ApplicationException):
    """Rate limiting exceptions."""

    def __init__(self, limit: int, window: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message     = f"Rate limit exceeded: {limit} requests per {window}",
            error_code  = "RATE_LIMIT_EXCEEDED",
            status_code = status.HTTP_429_TOO_MANY_REQUESTS,
            details     = {"limit": limit, "window": window, **(details or {})},
        )


class ConfigurationException(ApplicationException):
    """Configuration-related exceptions."""

    def __init__(self, setting: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message     = f"Configuration error: {setting}",
            error_code  = "CONFIGURATION_ERROR",
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            details     = {"setting": setting, **(details or {})},
        )


class ServiceUnavailableException(ApplicationException):
    """Service unavailable exceptions."""

    def __init__(self, service: str, reason: str = "Service temporarily unavailable"):
        super().__init__(
            message     = f"{service}: {reason}",
            error_code  = "SERVICE_UNAVAILABLE",
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
            details     = {"service": service, "reason": reason},
        )
