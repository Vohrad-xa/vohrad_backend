"""Centralized RBAC and access policy utilities."""

from __future__ import annotations
from constants.defaults import SecurityDefaults
from datetime import datetime
from typing import Set, Tuple

# Reserved role names to prevent conflicts with system roles
RESERVED_ROLE_NAMES: Set[str] = {
    "admin",
    "super_admin",
    "manager",
    "employee",
    "user",
    "viewer",
}

# Restricted permissions that tenants cannot assign
RESTRICTED_TENANT_PERMS: Set[Tuple[str, str]] = {
    ("tenant", "create"),
    ("tenant", "update"),
    ("tenant", "delete"),
    ("user", "delete"),
}


def is_reserved_role(name: str) -> bool:
    """Return True if role name is reserved."""
    normalized = (name or "").strip().lower()
    return normalized in RESERVED_ROLE_NAMES


def is_restricted_perm(resource: str, action: str) -> bool:
    """Return True for restricted (resource, action)."""
    return ((resource or "").strip(), (action or "").strip()) in RESTRICTED_TENANT_PERMS


def apply_conditional_access(permissions: set[str], resource: str) -> set[str]:
    """Apply conditional access checks to permissions.

    - Outside business hours, delete actions are removed.
    - If a resource is specified, permissions are filtered to those matching it.
    """
    current_hour = datetime.now().hour
    if not (
        SecurityDefaults.BUSINESS_HOUR_START
        <= current_hour
        <= SecurityDefaults.BUSINESS_HOUR_END
    ):
        permissions = {p for p in permissions if not p.endswith(".delete")}

    if resource:
        permissions = {
            p for p in permissions if permission_applies_to_resource(p, resource)
        }

    return permissions


def permission_applies_to_resource(permission: str, resource: str) -> bool:
    """Return True if *permission* covers the *resource*."""
    if permission == "*.*":
        return True

    perm_resource = permission.split(".")[0]
    return perm_resource == "*" or perm_resource == resource


def merge_permissions_with_precedence(
    tenant_perms: set[str], system_perms: set[str]
) -> set[str]:
    """Merge system and tenant permissions honoring tenant overrides."""
    effective = system_perms.copy()

    for perm in tenant_perms:
        if perm.startswith("-"):
            effective.discard(perm[1:])
        else:
            effective.add(perm)

    return effective
