"""RBAC policy constants and helpers (single source of truth).

This module centralizes reserved role names and restricted permission patterns
to avoid duplication and ensure consistent enforcement across services and
schemas.
"""

from __future__ import annotations
from typing import Set, Tuple

RESERVED_ROLE_NAMES: Set[str] = {
    "admin",
    "super_admin",
    "manager",
    "employee",
    "user",
    "viewer",
}
RESTRICTED_TENANT_PERMS: Set[Tuple[str, str]] = {
    ("tenant", "create"),
    ("tenant", "update"),
    ("tenant", "delete"),
    ("user", "delete"),
}


def is_reserved_role(name: str) -> bool:
    """Returns True if role name is reserved (case-insensitive)."""
    normalized = (name or "").strip().lower()
    return normalized in RESERVED_ROLE_NAMES


def is_restricted_perm(resource: str, action: str) -> bool:
    """Returns True if the (resource, action) pair is restricted in tenant context."""
    return ((resource or "").strip(), (action or "").strip()) in RESTRICTED_TENANT_PERMS
