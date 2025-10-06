"""Centralized error registry for enterprise-grade error handling."""

from dataclasses import dataclass
from fastapi import status
from typing import Dict, Final


@dataclass(frozen=True)
class ErrorDefinition:
    """Immutable error definition with all metadata."""

    code       : str
    message    : str
    status_code: int
    category   : str


class ErrorRegistry:
    """Centralized registry of all application errors."""

    ENTITY_NOT_FOUND: Final[ErrorDefinition] = ErrorDefinition(
        code        = "ENTITY_NOT_FOUND",
        message     = "Resource not found",
        status_code = status.HTTP_404_NOT_FOUND,
        category    = "domain",
    )

    ENTITY_ALREADY_EXISTS: Final[ErrorDefinition] = ErrorDefinition(
        code        = "ENTITY_ALREADY_EXISTS",
        message     = "Resource already exists",
        status_code = status.HTTP_409_CONFLICT,
        category    = "domain",
    )

    BUSINESS_RULE_VIOLATION: Final[ErrorDefinition] = ErrorDefinition(
        code        = "BUSINESS_RULE_VIOLATION",
        message     = "Business rule violation",
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
        category    = "domain",
    )

    INVALID_DOMAIN_STATE: Final[ErrorDefinition] = ErrorDefinition(
        code        = "INVALID_DOMAIN_STATE",
        message     = "Resource is in invalid state for this operation",
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
        category    = "domain",
    )

    AUTHENTICATION_FAILED: Final[ErrorDefinition] = ErrorDefinition(
        code        = "AUTHENTICATION_FAILED",
        message     = "Authentication failed",
        status_code = status.HTTP_401_UNAUTHORIZED,
        category    = "auth",
    )

    AUTHORIZATION_FAILED: Final[ErrorDefinition] = ErrorDefinition(
        code        = "AUTHORIZATION_FAILED",
        message     = "Access denied",
        status_code = status.HTTP_403_FORBIDDEN,
        category    = "auth",
    )

    RESTRICTED_PERMISSION: Final[ErrorDefinition] = ErrorDefinition(
        code        = "RESTRICTED_PERMISSION",
        message     = "Restricted permission by policy",
        status_code = status.HTTP_403_FORBIDDEN,
        category    = "auth",
    )

    VALIDATION_ERROR: Final[ErrorDefinition] = ErrorDefinition(
        code        = "VALIDATION_ERROR",
        message     = "Validation failed",
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
        category    = "validation",
    )

    DATABASE_ERROR: Final[ErrorDefinition] = ErrorDefinition(
        code        = "DATABASE_ERROR",
        message     = "Database operation failed",
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
        category    = "infrastructure",
    )

    EXTERNAL_SERVICE_ERROR: Final[ErrorDefinition] = ErrorDefinition(
        code        = "EXTERNAL_SERVICE_ERROR",
        message     = "External service error",
        status_code = status.HTTP_502_BAD_GATEWAY,
        category    = "infrastructure",
    )

    SERVICE_UNAVAILABLE: Final[ErrorDefinition] = ErrorDefinition(
        code        = "SERVICE_UNAVAILABLE",
        message     = "Service temporarily unavailable",
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
        category    = "infrastructure",
    )

    CONFIGURATION_ERROR: Final[ErrorDefinition] = ErrorDefinition(
        code        = "CONFIGURATION_ERROR",
        message     = "Configuration error",
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
        category    = "configuration",
    )

    RATE_LIMIT_EXCEEDED: Final[ErrorDefinition] = ErrorDefinition(
        code        = "RATE_LIMIT_EXCEEDED",
        message     = "Rate limit exceeded",
        status_code = status.HTTP_429_TOO_MANY_REQUESTS,
        category    = "rate_limit",
    )

    @classmethod
    def get_all_errors(cls) -> Dict[str, ErrorDefinition]:
        """Get all registered errors."""
        return {name: getattr(cls, name) for name in dir(cls) if isinstance(getattr(cls, name), ErrorDefinition)}

    @classmethod
    def get_by_code(cls, code: str) -> ErrorDefinition:
        """Get error definition by code."""
        for error_def in cls.get_all_errors().values():
            if error_def.code == code:
                return error_def
        raise ValueError(f"Unknown error code: {code}")
