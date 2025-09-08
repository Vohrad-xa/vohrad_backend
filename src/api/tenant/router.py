"""Tenant router."""

from api.auth import get_current_admin
from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_authenticated_context, get_shared_context
from api.permission.dependencies import require_permission
from api.tenant.schema import TenantCreate, TenantResponse, TenantSettingsUpdate, TenantUpdate
from api.tenant.service import tenant_service
from database.sessions import get_default_db_session
from fastapi import APIRouter, Depends, Query, status
from uuid import UUID
from web import (
    CreatedResponse,
    DeletedResponse,
    PaginatedResponse,
    PaginationParams,
    ResponseFactory,
    SuccessResponse,
    pagination_params,
)

routes = APIRouter(
    tags=["tenant"],
    prefix="/tenant",
)


@routes.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=CreatedResponse[TenantResponse],
)
async def create_tenant(
    tenant_data: TenantCreate,
    _admin=Depends(get_current_admin),
    _authorized: bool = Depends(require_permission("tenant", "create")),
    db=Depends(get_default_db_session),
):
    """Create a new tenant (admin access only)"""
    tenant = await tenant_service.create_tenant(db, tenant_data)
    return ResponseFactory.transform_and_respond(tenant, TenantResponse, "created")


@routes.get("/search", response_model=SuccessResponse[PaginatedResponse[TenantResponse]])
async def search_tenants(
    q: str = Query(..., min_length=2, description="Search term"),
    _admin=Depends(get_current_admin),
    _authorized: bool = Depends(require_permission("tenant", "read")),
    pagination: PaginationParams = Depends(pagination_params),
    db=Depends(get_default_db_session),
):
    """Search tenants by email, city, or industry (admin access only)"""
    tenants, total = await tenant_service.search(db, q, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(tenants, total, pagination, TenantResponse)


@routes.get("/", response_model=SuccessResponse[TenantResponse])
async def get_current_tenant_endpoint(context=Depends(get_authenticated_context)):
    """Get the current tenant"""
    _user, tenant = context
    return ResponseFactory.transform_and_respond(tenant, TenantResponse)


@routes.get(
    "/{tenant_id}",
    response_model=SuccessResponse[TenantResponse],
)
async def get_tenant_by_id(
    tenant_id: UUID,
    _admin=Depends(get_current_admin),
    _authorized: bool = Depends(require_permission("tenant", "read")),
    db=Depends(get_default_db_session),
):
    """Get tenant by ID (admin access only)"""
    tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
    return ResponseFactory.transform_and_respond(tenant, TenantResponse)


@routes.put("/", response_model=SuccessResponse[TenantResponse])
async def update_tenant(
    tenant_data: TenantUpdate,
    tenant_id  : UUID = Query(..., description="Tenant ID to update"),
    _admin=Depends(get_current_admin),
    _authorized: bool = Depends(require_permission("tenant", "update")),
    db=Depends(get_default_db_session),
):
    """Update tenant (admin access only)"""
    updated_tenant = await tenant_service.update_tenant_by_id(db, tenant_id, tenant_data)
    return ResponseFactory.transform_and_respond(updated_tenant, TenantResponse)


@routes.put("/{tenant_id}", response_model=SuccessResponse[TenantResponse])
async def update_tenant_by_id(
    tenant_id  : UUID,
    tenant_data: TenantUpdate,
    _admin=Depends(get_current_admin),
    _authorized: bool = Depends(require_permission("tenant", "update")),
    db=Depends(get_default_db_session),
):
    """Update tenant by ID (admin access only)"""
    updated_tenant = await tenant_service.update_tenant_by_id(db, tenant_id, tenant_data)
    return ResponseFactory.transform_and_respond(updated_tenant, TenantResponse)


@routes.put("/settings", response_model=SuccessResponse[TenantResponse])
async def update_tenant_settings(
    settings: TenantSettingsUpdate,
    context = Depends(get_shared_context),
    _authorized: bool = Depends(require_permission("tenant", "manage")),
):
    """Allow tenant managers to update timezone and working hours for their own tenant."""
    _current_user, tenant, db = context

    # Build a TenantUpdate with only the allowed fields
    data   = settings.model_dump(exclude_unset=True)
    update = TenantUpdate(**data)

    updated = await tenant_service.update_tenant(db, tenant, update)
    return ResponseFactory.transform_and_respond(updated, TenantResponse)


@routes.delete("/", response_model=DeletedResponse)
async def delete_tenant(
    tenant_id: UUID = Query(..., description="Tenant ID to delete"),
    _admin=Depends(get_current_admin),
    _authorized: bool = Depends(require_permission("tenant", "delete")),
    db=Depends(get_default_db_session),
):
    """Delete tenant (admin access only)"""
    await tenant_service.delete_tenant_by_id(db, tenant_id)
    return DeletedResponse()


@routes.delete("/{tenant_id}", response_model=DeletedResponse)
async def delete_tenant_by_id(
    tenant_id: UUID,
    _admin=Depends(get_current_admin),
    _authorized: bool = Depends(require_permission("tenant", "delete")),
    db=Depends(get_default_db_session),
):
    """Delete tenant by ID (admin access only)"""
    await tenant_service.delete_tenant_by_id(db, tenant_id)
    return DeletedResponse()
