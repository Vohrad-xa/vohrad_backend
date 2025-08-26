"""Business domain enumerations and choices."""

from enum import Enum

class UserRoles(Enum):
    """Enumeration of user roles."""

    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"

class TenantStatus(Enum):
    """Enumeration of tenant statuses."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
