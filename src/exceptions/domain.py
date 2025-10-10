"""Domain layer exceptions - Base classes for type checking."""

from .base import BaseAppException
from fastapi import status
from typing import Any, Dict, Optional


class DomainException(BaseAppException):
    """Base class for domain layer exceptions."""

    def __init__(
        self,
        message    : str,
        error_code : str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details    : Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, status_code, details)


class LicenseLimitExceededException(DomainException):
    """Raised when tenant has reached their license seat limit."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message     = message,
            error_code  = "LICENSE_LIMIT_EXCEEDED",
            status_code = status.HTTP_403_FORBIDDEN,
            details     = details,
        )
