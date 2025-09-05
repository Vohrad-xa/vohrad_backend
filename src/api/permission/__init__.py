"""Permission API module - enterprise RBAC management."""

from .models import Permission
from .router import routes
from .schema import PermissionCreate, PermissionListResponse, PermissionResponse, PermissionUpdate
from .service import PermissionService, permission_service

__all__ = [
    "Permission",
    "PermissionCreate",
    "PermissionListResponse",
    "PermissionResponse",
    "PermissionService",
    "PermissionUpdate",
    "permission_service",
    "routes",
]
