"""Exception handling system."""

from .application import ApplicationException, AuthenticationException, AuthorizationException
from .base import BaseAppException
from .domain import DomainException
from .factory import ExceptionFactory, invalid_credentials, tenant_not_found, user_not_found
from .infrastructure import InfrastructureException
from .integration import IntegrationException
from .jwt_exceptions import (
    JWTException,
    TokenExpiredException,
    TokenInvalidException,
    TokenMissingException,
    TokenRevokedException,
)
from .registry import ErrorDefinition, ErrorRegistry

__all__ = [
    # Base classes for type checking
    "ApplicationException",
    "AuthenticationException",
    "AuthorizationException",
    # Core system
    "BaseAppException",
    "DomainException",
    "ErrorDefinition",
    "ErrorRegistry",
    "ExceptionFactory",
    "InfrastructureException",
    "IntegrationException",
    # JWT exceptions
    "JWTException",
    "TokenExpiredException",
    "TokenInvalidException",
    "TokenMissingException",
    "TokenRevokedException",
    "invalid_credentials",
    # Convenience functions (recommended)
    "tenant_not_found",
    "user_not_found",
]
