"""Domain layer exceptions - Base classes for type checking."""

from typing import Any, Dict, Optional
from fastapi import status
from .base import BaseAppException

class DomainException(BaseAppException):
    """Base class for domain layer exceptions."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, error_code, status_code, details)
