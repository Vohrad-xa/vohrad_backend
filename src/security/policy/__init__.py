"""Centralized RBAC policy helpers and constants."""

from .permission_registry import (
    PermissionSupportLevel,
    get_support_level,
    is_allowed_for_custom_role,
)
from .policy import (
    RESERVED_ROLE_NAMES,
    RESTRICTED_TENANT_PERMS,
    apply_conditional_access,
    is_reserved_role,
    is_restricted_perm,
    merge_permissions_with_precedence,
    permission_applies_to_resource,
)

__all__ = [
    "RESERVED_ROLE_NAMES",
    "RESTRICTED_TENANT_PERMS",
    "PermissionSupportLevel",
    "apply_conditional_access",
    "get_support_level",
    "is_allowed_for_custom_role",
    "is_reserved_role",
    "is_restricted_perm",
    "merge_permissions_with_precedence",
    "permission_applies_to_resource",
]
