"""Middleware components."""

from .decorators import with_database_session
from .exception_handler import ExceptionHandler
from .logging_middleware import RequestLoggingMiddleware
from security.password import PasswordManager, hash_password, password_manager, verify_password

# JWT middleware is now in security.jwt.middleware
# from security.jwt.middleware import JWTAuthMiddleware

__all__ = [
    "ExceptionHandler",
    "PasswordManager",
    "RequestLoggingMiddleware",
    "hash_password",
    "password_manager",
    "verify_password",
    "with_database_session",
]
