"""Role API module - enterprise RBAC management."""

from .models import Role
from .router import routes
from .schema import RoleCreate
from .schema import RoleListResponse
from .schema import RoleResponse
from .schema import RoleUpdate
from .service import RoleService
from .service import role_service

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
