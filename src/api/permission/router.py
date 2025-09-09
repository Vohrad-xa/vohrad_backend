"""Permission router."""

from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_tenant_context
from api.permission.dependencies import RequireRoleManagement
from api.permission.schema import PermissionCreate, PermissionResponse, PermissionUpdate
from api.permission.service import permission_service
from fastapi import APIRouter, Depends, Query, status
from uuid import UUID
from web import (
    CreatedResponse,
    DeletedResponse,
    PaginatedResponse,
    PaginationParams,
    ResponseFactory,
    SuccessResponse,
    get_if_match_header,
    pagination_params,
)

routes = APIRouter(
    tags   = ["permissions"],
    prefix = "/permissions",
)


@routes.post(
    "/",
    status_code    = status.HTTP_201_CREATED,
    response_model = CreatedResponse[PermissionResponse],
)
async def create_permission(
    permission_data: PermissionCreate,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireRoleManagement),
):
    """Create new permission"""
    _, _tenant, db = context
    permission = await permission_service.create_permission(db, permission_data)
    return ResponseFactory.created(permission, response_model=PermissionResponse)


@routes.get(
    "/search",
    response_model = SuccessResponse[PaginatedResponse[PermissionResponse]],
)
async def search_permissions(
    q: str = Query(..., min_length=1, description="Search term"),
    pagination: PaginationParams = Depends(pagination_params),
    context = Depends(get_tenant_context),
):
    """Search permissions by resource or action"""
    _, _tenant, db = context
    permissions, total = await permission_service.search_permissions(db, q, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(permissions, total, pagination, PermissionResponse)


@routes.get(
    "/role/{role_id}",
    response_model = SuccessResponse[list[PermissionResponse]],
)
async def get_role_permissions(
    role_id: UUID,
    context = Depends(get_tenant_context),
):
    """Get all permissions for a specific role"""
    _, _tenant, db = context
    permissions = await permission_service.get_role_permissions(db, role_id)
    return ResponseFactory.success(data=permissions, response_model=PermissionResponse)


@routes.get(
    "/resource/{resource}",
    response_model = SuccessResponse[list[PermissionResponse]],
)
async def get_permissions_by_resource(
    resource: str,
    context = Depends(get_tenant_context),
):
    """Get all permissions for a specific resource"""
    _, _tenant, db = context
    permissions = await permission_service.get_permissions_by_resource(db, resource)
    return ResponseFactory.success(data=permissions, response_model=PermissionResponse)


@routes.get(
    "/{permission_id}",
    response_model = SuccessResponse[PermissionResponse],
)
async def get_permission(
    permission_id: UUID,
    context = Depends(get_tenant_context),
):
    """Get permission by ID"""
    _, _tenant, db = context
    permission = await permission_service.get_permission_by_id(db, permission_id)
    return ResponseFactory.success(permission, response_model=PermissionResponse)


@routes.get(
    "/",
    response_model = SuccessResponse[PaginatedResponse[PermissionResponse]],
)
async def get_permissions(
    pagination: PaginationParams = Depends(pagination_params),
    context = Depends(get_tenant_context),
):
    """Get paginated list of permissions"""
    _, _tenant, db = context
    permissions, total = await permission_service.get_permissions_paginated(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(permissions, total, pagination, PermissionResponse)


@routes.put(
    "/{permission_id}",
    response_model = SuccessResponse[PermissionResponse],
)
async def update_permission(
    permission_id  : UUID,
    permission_data: PermissionUpdate,
    context = Depends(get_tenant_context),
    _authorized: bool = Depends(RequireRoleManagement),
):
    """Update permission"""
    _, _tenant, db = context
    permission = await permission_service.update_permission(db, permission_id, permission_data)
    return ResponseFactory.updated(permission, response_model=PermissionResponse)


@routes.delete("/{permission_id}", response_model=DeletedResponse)
async def delete_permission(
    permission_id: UUID,
    context = Depends(get_tenant_context),
    _authorized: bool = Depends(RequireRoleManagement),
    if_match: str | None = Depends(get_if_match_header),
):
    """Remove permission"""
    _, _tenant, db = context
    await permission_service.delete_permission(db, permission_id, etag=if_match)
    return ResponseFactory.deleted("permission")
