"""Enterprise exception factory for clean, automated error handling."""

from .base import BaseAppException
from .registry import ErrorDefinition, ErrorRegistry
from typing import Any, Dict, Optional
from uuid import uuid4


class ExceptionFactory:
    """Factory for creating standardized exceptions with minimal boilerplate."""

    @staticmethod
    def create(
        error_def             : ErrorDefinition,
        details               : Optional[Dict[str, Any]] = None,
        context               : Optional[str] = None,
        correlation_id        : Optional[str] = None,
        use_context_as_message: bool = False,
    ) -> BaseAppException:
        """Create standardized exception from error definition."""
        if use_context_as_message and context:
            message = context
        else:
            message = error_def.message
            if context:
                message = f"{message}: {context}"

        return BaseAppException(
            message        = message,
            error_code     = error_def.code,
            status_code    = error_def.status_code,
            details        = details or {},
            correlation_id = correlation_id or str(uuid4()),
        )

    @staticmethod
    def not_found(entity_type: str, identifier: Any = None) -> BaseAppException:
        """Create entity not found exception."""
        return ExceptionFactory.create(
            ErrorRegistry.ENTITY_NOT_FOUND,
            details                = {"entity_type": entity_type, "identifier": str(identifier) if identifier else None},
            context                = f"{entity_type} not found",
            use_context_as_message = True,
        )

    @staticmethod
    def already_exists(entity_type: str, field: str, value: Any) -> BaseAppException:
        """Create entity already exists exception."""
        return ExceptionFactory.create(
            ErrorRegistry.ENTITY_ALREADY_EXISTS,
            details = {"entity_type": entity_type, "field": field, "value": str(value)},
            context = f"{entity_type} with {field} '{value}' already exists",
        )

    @staticmethod
    def business_rule(rule_description: str, details: Optional[Dict[str, Any]] = None) -> BaseAppException:
        """Create business rule violation exception."""
        return ExceptionFactory.create(ErrorRegistry.BUSINESS_RULE_VIOLATION, details=details, context=rule_description)

    @staticmethod
    def invalid_state(entity_type: str, current_state: str, required_state: str) -> BaseAppException:
        """Create invalid domain state exception."""
        return ExceptionFactory.create(
            ErrorRegistry.INVALID_DOMAIN_STATE,
            details = {"entity_type": entity_type, "current_state": current_state, "required_state": required_state},
            context = f"{entity_type} is '{current_state}', requires '{required_state}'",
        )

    @staticmethod
    def authentication_failed(reason: Optional[str] = None) -> BaseAppException:
        """Create authentication failed exception."""
        return ExceptionFactory.create(ErrorRegistry.AUTHENTICATION_FAILED, context=reason)

    @staticmethod
    def authorization_failed(resource: str, action: str) -> BaseAppException:
        """Create authorization failed exception."""
        return ExceptionFactory.create(
            ErrorRegistry.AUTHORIZATION_FAILED,
            details = {"resource": resource, "action": action},
            context = f"Cannot {action} {resource}",
        )

    @staticmethod
    def restricted_permission(resource: str, action: str) -> BaseAppException:
        """Create restricted-permission exception (policy-enforced 403)."""
        return ExceptionFactory.create(
            ErrorRegistry.RESTRICTED_PERMISSION,
            details = {"resource": resource, "action": action},
            context = f"Restricted by policy: cannot {action} {resource}",
        )

    @staticmethod
    def validation_failed(field: str, reason: str) -> BaseAppException:
        """Create validation error exception."""
        return ExceptionFactory.create(
            ErrorRegistry.VALIDATION_ERROR,
            details = {"field": field, "reason": reason},
            context = f"Field '{field}': {reason}",
        )

    @staticmethod
    def database_error(operation: str, details: Optional[Dict[str, Any]] = None) -> BaseAppException:
        """Create database error exception."""
        return ExceptionFactory.create(
            ErrorRegistry.DATABASE_ERROR,
            details = {"operation": operation, **(details or {})},
            context = f"Database operation failed: {operation}",
        )

    @staticmethod
    def external_service_error(service: str, operation: str, details: Optional[Dict[str, Any]] = None) -> BaseAppException:
        """Create external service error exception."""
        return ExceptionFactory.create(
            ErrorRegistry.EXTERNAL_SERVICE_ERROR,
            details = {"service": service, "operation": operation, **(details or {})},
            context = f"Service '{service}' failed during {operation}",
        )

    @staticmethod
    def service_unavailable(service: str, reason: Optional[str] = None) -> BaseAppException:
        """Create service unavailable exception."""
        return ExceptionFactory.create(
            ErrorRegistry.SERVICE_UNAVAILABLE,
            details = {"service": service, "reason": reason},
            context = f"Service '{service}' unavailable" + (f": {reason}" if reason else ""),
        )


# Convenience functions for common patterns
def tenant_not_found(identifier: Any = None) -> BaseAppException:
    """Shorthand for tenant not found."""
    return ExceptionFactory.not_found("Tenant", identifier)


def user_not_found(identifier: Any = None) -> BaseAppException:
    """Shorthand for user not found."""
    return ExceptionFactory.not_found("User", identifier)


def invalid_credentials() -> BaseAppException:
    """Shorthand for invalid credentials."""
    return ExceptionFactory.authentication_failed("Invalid credentials")
