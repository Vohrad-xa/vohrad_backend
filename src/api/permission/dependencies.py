"""Permission dependencies for route-level authorization."""

from api.auth import get_current_user
from exceptions import ExceptionFactory
from fastapi import Depends
from security.authorization import authorization_service
from security.jwt import AuthenticatedUser
from typing import Callable


def require_role(role_name: str) -> Callable:
    """Direct role check dependency factory."""

    async def role_dependency(current_user: AuthenticatedUser = Depends(get_current_user)) -> bool:
        has_role = await authorization_service.user_has_role(current_user.user_id, role_name, current_user.tenant_id)

        if not has_role:
            raise ExceptionFactory.authorization_failed("role", role_name)

        return True

    return role_dependency


def require_permission(resource: str, action: str) -> Callable:
    """Direct permission check dependency factory."""

    async def permission_dependency(
        current_user: AuthenticatedUser = Depends(get_current_user)
    ) -> bool:
        has_permission = await authorization_service.user_has_permission(
            current_user.user_id, resource, action, current_user.tenant_id
        )

        if not has_permission:
            raise ExceptionFactory.authorization_failed(resource, action)

        return True

    return permission_dependency


"""Role-based dependencies"""
RequireSuperAdmin = require_role("super_admin")
RequireAdmin      = require_role("admin")
RequireManager    = require_role("manager")

"""Permission-based dependencies"""
RequireUserManagement     = require_permission("user", "*")
RequireUserRead           = require_permission("user", "read")
RequireUserCreate         = require_permission("user", "create")
RequireUserUpdate         = require_permission("user", "update")
RequireTenantManagement   = require_permission("tenant", "*")
RequireRoleManagement     = require_permission("role", "*")
RequireItemManagement     = require_permission("item", "*")
RequireItemCreate         = require_permission("item", "create")
RequireItemUpdate         = require_permission("item", "update")
RequireItemDelete         = require_permission("item", "delete")
RequireLocationManagement = require_permission("location", "*")
RequireLocationCreate     = require_permission("location", "create")
RequireLocationUpdate     = require_permission("location", "update")
RequireLocationDelete     = require_permission("location", "delete")
