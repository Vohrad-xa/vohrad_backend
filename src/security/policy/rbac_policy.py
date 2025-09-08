"""RBAC policy constants and helpers."""

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
    """Return True if role name is reserved."""
    normalized = (name or "").strip().lower()
    return normalized in RESERVED_ROLE_NAMES


def is_restricted_perm(resource: str, action: str) -> bool:
    """Return True for restricted (resource, action)."""
    return ((resource or "").strip(), (action or "").strip()) in RESTRICTED_TENANT_PERMS
