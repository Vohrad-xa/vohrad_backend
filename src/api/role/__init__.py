"""Role API module - enterprise RBAC management."""

from .models import Role
from .router import routes
from .schema import RoleCreate, RoleListResponse, RoleResponse, RoleUpdate
from .service import RoleService, role_service

__all__ = [
    "Role",
    "RoleCreate",
    "RoleListResponse",
    "RoleResponse",
    "RoleService",
    "RoleUpdate",
    "role_service",
    "routes",
]
