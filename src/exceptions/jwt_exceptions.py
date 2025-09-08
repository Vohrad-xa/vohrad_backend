"""JWT-specific exceptions following enterprise error handling patterns."""

from .application import AuthenticationException
from typing import Any, Dict, Optional


class JWTException(AuthenticationException):
    """Base JWT exception."""

    def __init__(
        self,
        message   : str,
        error_code: str = "JWT_ERROR",
        details   : Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.error_code = error_code


class TokenExpiredException(JWTException):
    """Token has expired."""

    def __init__(self, message: str = "Token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="TOKEN_EXPIRED", details=details)


class TokenInvalidException(JWTException):
    """Token is invalid or malformed."""

    def __init__(self, message: str = "Invalid token", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="TOKEN_INVALID", details=details)


class TokenMissingException(JWTException):
    """Token is missing from request."""

    def __init__(self, message: str = "Authentication token required", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, error_code="TOKEN_MISSING", details=details)


class TokenRevokedException(JWTException):
    """Token has been revoked."""

    def __init__(self, token_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message="Token has been revoked", error_code="TOKEN_REVOKED", details={"token_id": token_id, **(details or {})}
        )
