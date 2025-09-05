"""Business domain enumerations and choices."""

from enum import Enum


class RoleType(Enum):
    """Role type enumeration."""

    BASIC      = "BASIC"
    PREDEFINED = "PREDEFINED"
    CUSTOM     = "CUSTOM"


class RoleScope(Enum):
    """Role scope enumeration."""

    GLOBAL = "GLOBAL"  # Database value: "GLOBAL"
    TENANT = "TENANT"  # Database value: "TENANT"


class UserRoles(Enum):
    """Enumeration of user roles."""

    ADMIN   = "admin"
    MANAGER = "manager"
    USER    = "user"
    VIEWER  = "viewer"


class TenantStatus(Enum):
    """Enumeration of tenant statuses."""

    ACTIVE    = "active"
    INACTIVE  = "inactive"
    SUSPENDED = "suspended"
