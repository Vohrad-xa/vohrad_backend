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
