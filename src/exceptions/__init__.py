"""Enterprise-grade exception handling system.

Usage:
    from exceptions import ExceptionFactory, tenant_not_found, user_not_found

    # Using factory (recommended for new code)
    raise ExceptionFactory.not_found("User", user_id)
    raise ExceptionFactory.already_exists("User", "email", email)

    # Using convenience functions (most common patterns)
    raise tenant_not_found(tenant_id)
    raise user_not_found(user_id)
    raise duplicate_email(email)
"""

# Core components
# Base classes needed for type checking
from .application import ApplicationException
from .base import BaseAppException
from .domain import DomainException
from .factory import ExceptionFactory
from .factory import duplicate_email
from .factory import duplicate_subdomain
from .factory import invalid_credentials
from .factory import tenant_not_found
from .factory import user_not_found
from .infrastructure import InfrastructureException
from .integration import IntegrationException
from .registry import ErrorDefinition
from .registry import ErrorRegistry

__all__ = [
    # Base classes for type checking
    "ApplicationException",
    # Core system
    "BaseAppException",
    "DomainException",
    "ErrorDefinition",
    "ErrorRegistry",
    "ExceptionFactory",
    "InfrastructureException",
    "IntegrationException",
    "duplicate_email",
    "duplicate_subdomain",
    "invalid_credentials",
    # Convenience functions (recommended)
    "tenant_not_found",
    "user_not_found",
]
