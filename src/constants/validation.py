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

    # Tenant fields
    MAX_TENANT_NAME_LENGTH: Final[int] = 100
    MIN_TENANT_NAME_LENGTH: Final[int] = 2
    MAX_DESCRIPTION_LENGTH: Final[int] = 500
