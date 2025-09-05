"""Database constraint violation handler."""

from exceptions import ExceptionFactory
import re
from sqlalchemy.exc import IntegrityError
from typing import Any, Dict, Optional


class ConstraintViolationHandler:
    """Handles database constraint violations dynamically."""

    def __init__(self):
        # Dynamic mappings
        self._constraint_entity_mapping = {
            r".*email.*"      : "User",
            r".*subdomain.*"  : "Tenant",
            r".*name.*"       : lambda ctx  : self._determine_entity_from_context(ctx),
            r".*permissions.*": "Permission",
        }

        self._context_field_mapping = {
            "email"     : "email",
            "subdomain" : "subdomain",
            "sub_domain": "subdomain",
            "name"      : "name",
            "resource"  : "resource and action",  # Special case for permissions
        }

    def handle_violation(self, error: IntegrityError, operation_context: Dict[str, Any]) -> Exception:
        """Handle database constraint violations."""
        constraint_name = self._extract_constraint_name(error)
        error_str       = str(error.orig) if error.orig else str(error)
        error_lower     = error_str.lower()

        if "foreign key constraint" in error_lower or "violates foreign key" in error_lower:
            return self._handle_foreign_key_violation(error_lower, operation_context)

        if "duplicate key" in error_lower or "already exists" in error_lower:
            return self._handle_unique_constraint_violation(constraint_name, error_lower, operation_context)

        raise error

    def _handle_foreign_key_violation(self, error_str: str, context: Dict[str, Any]) -> Exception:
        """Handle foreign key violations."""
        if "role" in error_str or context.get("role_id"):
            return ExceptionFactory.not_found("Role", str(context.get("role_id", "unknown")))
        if "tenant" in error_str or context.get("tenant_id"):
            return ExceptionFactory.not_found("Tenant", str(context.get("tenant_id", "unknown")))
        if "user" in error_str or context.get("user_id"):
            return ExceptionFactory.not_found("User", str(context.get("user_id", "unknown")))

        return ExceptionFactory.not_found("Entity", "unknown")

    def _handle_unique_constraint_violation(
        self, constraint_name: Optional[str], error_str: str, context: Dict[str, Any]
    ) -> Exception:
        """Handle unique constraint violations."""
        if constraint_name:
            entity_type = self._get_entity_from_constraint(constraint_name, context)
            field_name  = self._get_field_from_constraint(constraint_name, context)
            field_value = self._get_field_value_from_context(field_name, context)

            if entity_type and field_name and field_value:
                return ExceptionFactory.already_exists(entity_type, field_name, field_value)

        # Fallback analysis
        return self._analyze_error_message_dynamically(error_str, context)

    def _get_entity_from_constraint(self, constraint_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Extract entity type from constraint name."""
        constraint_lower = constraint_name.lower()

        for pattern, entity in self._constraint_entity_mapping.items():
            if re.match(pattern, constraint_lower):
                if callable(entity):
                    return entity(context)
                return entity
        return None

    def _get_field_from_constraint(self, constraint_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Extract field name from constraint."""
        constraint_lower = constraint_name.lower()
        for field_key, field_display in self._context_field_mapping.items():
            if field_key in constraint_lower:
                return field_display
        return None

    def _get_field_value_from_context(self, field_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Extract field value from context."""
        if field_name == "resource and action":
            resource = context.get("resource", "unknown")
            action   = context.get("action", "unknown")
            return f"{resource}:{action}"

        for context_key in ["email", "subdomain", "sub_domain", "name"]:
            if context_key in field_name.lower() and context.get(context_key):
                return str(context.get(context_key))

        return "unknown"

    def _determine_entity_from_context(self, context: Dict[str, Any]) -> str:
        """Extract entity type from operation context."""
        operation = context.get("operation", "")
        if "user" in operation:
            return "User"
        if "role" in operation:
            return "Role"
        if "tenant" in operation:
            return "Tenant"
        if "permission" in operation:
            return "Permission"
        return "Entity"

    def _analyze_error_message_dynamically(self, error_str: str, context: Dict[str, Any]) -> Exception:
        """Fallback error message analysis."""
        entity_type = self._determine_entity_from_context(context)
        field_name, field_value = self._get_most_relevant_field(context)

        return ExceptionFactory.already_exists(entity_type, field_name, field_value)

    def _get_most_relevant_field(self, context: Dict[str, Any]) -> tuple[str, str]:
        """Extract most relevant field from context."""
        field_priority = ["email", "subdomain", "sub_domain", "name", "resource"]

        for field in field_priority:
            if context.get(field):
                display_name = self._context_field_mapping.get(field, field)
                value        = str(context.get(field))

                if field == "resource" and context.get("action"):
                    return "resource and action", f"{value}:{context.get('action')}"

                return display_name, value

        return "field", "unknown"

    def _extract_constraint_name(self, error: IntegrityError) -> Optional[str]:
        """Extract constraint name from database error."""
        error_str = str(error.orig) if error.orig else str(error)
        patterns = [
            r'duplicate key value violates unique constraint "([^"]+)"',
            r'violates unique constraint "([^"]+)"',
            r'violates foreign key constraint "([^"]+)"',
            r'constraint "([^"]+)"',
        ]

        for pattern in patterns:
            if match := re.search(pattern, error_str):
                return match.group(1)

        return None


constraint_handler = ConstraintViolationHandler()
