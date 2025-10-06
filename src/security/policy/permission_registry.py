"""Permission support-level registry for custom roles.

Defines allowlist and support levels for `resource.action` pairs used by CUSTOM roles.
This prevents introducing invalid/untested permissions in production.
"""

from __future__ import annotations
from config.settings import get_settings
from enum import Enum
from typing import Dict, Tuple


class PermissionSupportLevel(Enum):
    SUPPORTED     = "SUPPORTED"
    TESTING       = "TESTING"
    NOT_SUPPORTED = "NOT_SUPPORTED"


PERMISSION_SUPPORT_REGISTRY: Dict[Tuple[str, str], PermissionSupportLevel] = {
    ("user", "read")        : PermissionSupportLevel.SUPPORTED,
    ("user", "update")      : PermissionSupportLevel.SUPPORTED,
    ("user", "create")      : PermissionSupportLevel.SUPPORTED,
    ("role", "read")        : PermissionSupportLevel.SUPPORTED,
    ("role", "manage")      : PermissionSupportLevel.SUPPORTED,
    ("permission", "read")  : PermissionSupportLevel.SUPPORTED,
    ("permission", "manage"): PermissionSupportLevel.SUPPORTED,
    ("system", "read")      : PermissionSupportLevel.SUPPORTED,
}


def get_support_level(resource: str, action: str) -> PermissionSupportLevel | None:
    """Return support level for a resource.action pair, or None if unknown."""
    key = ((resource or "").strip().lower(), (action or "").strip().lower())
    return PERMISSION_SUPPORT_REGISTRY.get(key)


def is_allowed_for_custom_role(resource: str, action: str) -> tuple[bool, str | None]:
    """Check whether a permission is allowed for CUSTOM roles in current environment."""
    level = get_support_level(resource, action)
    if level is None or level == PermissionSupportLevel.NOT_SUPPORTED:
        return False, "Permission not supported for custom roles"

    if level == PermissionSupportLevel.SUPPORTED:
        return True, None

    # TESTING level
    env = get_settings().ENVIRONMENT
    if str(env).lower() == "production":
        return False, "Permission level TESTING is not allowed in production"
    return True, None
