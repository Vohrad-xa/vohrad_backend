"""Validation constraints and rules."""

from typing import Final


class ValidationConstraints:
    """Validation constraints for various fields."""

    # User fields
    MIN_PASSWORD_LENGTH: Final[int] = 8
    MAX_PASSWORD_LENGTH: Final[int] = 128
    MAX_NAME_LENGTH    : Final[int] = 50
    MIN_NAME_LENGTH    : Final[int] = 1
    MAX_EMAIL_LENGTH   : Final[int] = 254
    MAX_PHONE_LENGTH   : Final[int] = 20

    # Role fields
    DEFAULT_ROLE_LENGTH: Final[int] = 32
    MIN_ROLE_LENGTH    : Final[int] = 2
    MAX_ROLE_LENGTH    : Final[int] = 50

    # Permission fields
    MAX_RESOURCE_LENGTH: Final[int] = 50
    MAX_ACTION_LENGTH  : Final[int] = 50

    # Tenant fields
    MAX_TENANT_NAME_LENGTH: Final[int]  = 100
    MIN_TENANT_NAME_LENGTH: Final[int]  = 2
    MAX_DESCRIPTION_LENGTH: Final[int]  = 500
    MIN_SUBDOMAIN_LENGTH  : Final[int] = 1

    # Password requirements
    SPECIAL_CHARS: Final[str] = "!@#$%^&*()_+-=[]{}|;:,.<>?"
