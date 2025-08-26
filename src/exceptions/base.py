"""Base exception classes with structured metadata."""

from abc import ABC
from typing import Any, Dict, Optional
from fastapi import status

class BaseAppException(Exception, ABC):
    """Base exception for all application-specific errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.correlation_id = correlation_id
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
            "correlation_id": self.correlation_id,
            "exception_type": self.__class__.__name__,
        }
