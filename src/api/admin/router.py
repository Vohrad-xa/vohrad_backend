"""Admin routes with tenant context switching."""

from .dependencies import get_admin_params
from .service import admin_service
from api.permission import PermissionResponse, permission_service
from api.role import RoleResponse, role_service
from api.tenant import TenantResponse, TenantUpdate, tenant_service
from api.user.schema import UserResponse
from api.user.service import user_service
from fastapi import APIRouter, Depends, Query
from typing import Any, Optional
from uuid import UUID
from web import (
    DeletedResponse,
    PaginatedResponse,
    ResponseFactory,
    SuccessResponse,
    UpdatedResponse,
)

routes = APIRouter(
    tags   = ["admin"],
    prefix = "/admin",
)


@routes.get("/tenants", response_model = SuccessResponse[PaginatedResponse[Any]])
async def list_all_tenants(params = Depends(get_admin_params)):
    """List all tenants."""
    pagination, context = params
    return await admin_service.paginated_call(
        context, tenant_service.get_multi, pagination, TenantResponse
    )


@routes.get("/users", response_model=SuccessResponse[PaginatedResponse[Any]])
async def list_users(
    params = Depends(get_admin_params),
    scope: Optional[str] = Query(None)
):
    """List global users or tenant users."""
    pagination, context = params
    return await admin_service.paginated_call(
        context,
        user_service.get_multi,
        pagination,
        UserResponse,
        tenant_id = context.tenant_id,
        scope     = scope
    )


@routes.get("/roles", response_model=SuccessResponse[PaginatedResponse[Any]])
async def list_all_roles(
    params = Depends(get_admin_params),
    scope: Optional[str] = Query(None)
):
    """List all roles."""
    pagination, context = params
    return await admin_service.paginated_call(
        context,
        role_service.get_multi,
        pagination,
        RoleResponse,
        scope=scope
    )


@routes.get("/permissions", response_model = SuccessResponse[PaginatedResponse[Any]])
async def list_all_permissions(
    params = Depends(get_admin_params),
    scope: Optional[str] = Query(None)
):
    """List all permissions."""
    pagination, context = params
    return await admin_service.paginated_call(
        context,
        permission_service.get_multi,
        pagination,
        PermissionResponse,
        scope=scope
    )


@routes.put("/tenants/{tenant_id}", response_model=UpdatedResponse[TenantResponse])
async def update_tenant(
    tenant_id: UUID,
    tenant_data: TenantUpdate,
    params = Depends(get_admin_params)
) -> SuccessResponse[TenantResponse]:
    """Update tenant by ID (admin access only)."""
    _, context = params
    updated_tenant = await tenant_service.update_tenant_by_id(context.db_session, tenant_id, tenant_data)
    return ResponseFactory.updated(updated_tenant, response_model=TenantResponse)


@routes.delete("/tenants/{tenant_id}", response_model = DeletedResponse)
async def delete_tenant(
    tenant_id: UUID,
    params = Depends(get_admin_params)
) -> DeletedResponse:
    """Delete tenant."""
    _, context = params
    await tenant_service.delete_tenant_by_id(context.db_session, tenant_id)
    return ResponseFactory.deleted("tenant")


@routes.get("/tenant-context", response_model = SuccessResponse[dict])
async def get_current_tenant_context(params = Depends(get_admin_params)):
    """Get current tenant context."""
    _, context = params
    context_info = await admin_service.get_admin_context_info(context)
    return ResponseFactory.success(context_info)
