"""User-facing messages for validation, errors, and success responses."""

from typing import Final
from .defaults import TenantDefaults
from .validation import ValidationConstraints

class ValidationMessages:
    """Standardized validation error messages."""

    # Password messages
    PASSWORD_TOO_SHORT: Final[str] = (
        f"Password must be at least {ValidationConstraints.MIN_PASSWORD_LENGTH} characters long"
    )
    PASSWORD_TOO_LONG: Final[str] = (
        f"Password must be no more than {ValidationConstraints.MAX_PASSWORD_LENGTH} characters long"
    )
    PASSWORD_REQUIRED: Final[str] = "Password is required"

    # Name messages
    NAME_TOO_SHORT: Final[str] = f"Name must be at least {ValidationConstraints.MIN_NAME_LENGTH} character long"
    NAME_TOO_LONG: Final[str] = f"Name must be no more than {ValidationConstraints.MAX_NAME_LENGTH} characters long"
    NAME_REQUIRED: Final[str] = "Name is required"

    # Email messages
    EMAIL_INVALID: Final[str] = "Please provide a valid email address"
    EMAIL_TOO_LONG: Final[str] = f"Email must be no more than {ValidationConstraints.MAX_EMAIL_LENGTH} characters long"
    EMAIL_REQUIRED: Final[str] = "Email address is required"

    # Tenant messages
    SUBDOMAIN_INVALID: Final[str] = "Subdomain can only contain letters, numbers, and hyphens"
    SUBDOMAIN_TOO_SHORT: Final[str] = (
        f"Subdomain must be at least {TenantDefaults.MIN_SUBDOMAIN_LENGTH} characters long"
    )
    SUBDOMAIN_TOO_LONG: Final[str] = (
        f"Subdomain must be no more than {TenantDefaults.MAX_SUBDOMAIN_LENGTH} characters long"
    )
    TENANT_NAME_REQUIRED: Final[str] = "Tenant name is required"

class HTTPStatusMessages:
    """Standard HTTP response messages."""

    # Success messages
    RESOURCE_CREATED: Final[str] = "Resource created successfully"
    RESOURCE_UPDATED: Final[str] = "Resource updated successfully"
    RESOURCE_DELETED: Final[str] = "Resource deleted successfully"
    OPERATION_SUCCESS: Final[str] = "Operation completed successfully"

    # Error messages
    RESOURCE_NOT_FOUND: Final[str] = "Resource not found"
    ACCESS_DENIED: Final[str] = "Access denied"
    INVALID_REQUEST: Final[str] = "Invalid request data"
    INTERNAL_ERROR: Final[str] = "Internal server error occurred"

    # Authentication messages
    AUTH_REQUIRED: Final[str] = "Authentication required"
    AUTH_INVALID: Final[str] = "Invalid authentication credentials"
    TOKEN_EXPIRED: Final[str] = "Authentication token has expired"
