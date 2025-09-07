from api.auth import get_current_admin
from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_authenticated_context
from api.permission.dependencies import require_permission
from api.tenant.schema import TenantCreate, TenantResponse, TenantUpdate
from api.tenant.service import tenant_service
from database.sessions import get_default_db_session
from fastapi import APIRouter, Depends, Query, status
from uuid import UUID
from web import PaginationParams, ResponseFactory, pagination_params

routes = APIRouter(
    tags   = ["tenant"],
    prefix = "/tenant",
)


@routes.post("/", status_code=status.HTTP_201_CREATED)
async def create_tenant(
        tenant_data: TenantCreate,
        _admin = Depends(get_current_admin),
        _authorized: bool = Depends(require_permission('tenant', 'create')),
        db=Depends(get_default_db_session),
):
    """Create a new tenant (admin access only)"""
    tenant = await tenant_service.create_tenant(db, tenant_data)
    return ResponseFactory.transform_and_respond(tenant, TenantResponse, "created")


@routes.get("/search")
async def search_tenants(
        q: str = Query(..., min_length=2, description="Search term"),
        pagination: PaginationParams = Depends(pagination_params),
        _admin = Depends(get_current_admin),
        _authorized: bool = Depends(require_permission('tenant', 'read')),
        db=Depends(get_default_db_session),
):
    """Search tenants by email, city, or industry (admin access only)"""
    tenants, total = await tenant_service.search(db, q, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(tenants, total, pagination, TenantResponse)


@routes.get("/list")
async def get_tenants(
        pagination: PaginationParams = Depends(pagination_params),
        _admin = Depends(get_current_admin),
        _authorized: bool = Depends(require_permission('tenant', 'read')),
        db=Depends(get_default_db_session),
):
    """Get a paginated list of tenants (admin access only)"""
    tenants, total = await tenant_service.get_multi(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(tenants, total, pagination, TenantResponse)


@routes.get("/")
async def get_current_tenant_endpoint(context=Depends(get_authenticated_context)):
    """Get the current tenant"""
    _user, tenant = context
    return ResponseFactory.transform_and_respond(tenant, TenantResponse)


@routes.get("/{tenant_id}")
async def get_tenant_by_id(
        tenant_id: UUID,
        _admin = Depends(get_current_admin),
        _authorized: bool = Depends(require_permission('tenant', 'read')),
        db=Depends(get_default_db_session),
):
    """Get tenant by ID (admin access only)"""
    tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
    return ResponseFactory.transform_and_respond(tenant, TenantResponse)


@routes.put("/")
async def update_tenant(
        tenant_data: TenantUpdate,
        tenant_id: UUID = Query(..., description="Tenant ID to update"),
        _admin = Depends(get_current_admin),
        _authorized: bool = Depends(require_permission('tenant', 'update')),
        db=Depends(get_default_db_session),
):
    """Update tenant (admin access only)"""
    updated_tenant = await tenant_service.update_tenant_by_id(db, tenant_id, tenant_data)
    return ResponseFactory.transform_and_respond(updated_tenant, TenantResponse)


@routes.put("/{tenant_id}")
async def update_tenant_by_id(
        tenant_id  : UUID,
        tenant_data: TenantUpdate,
        _admin = Depends(get_current_admin),
        _authorized: bool = Depends(require_permission('tenant', 'update')),
        db=Depends(get_default_db_session),
):
    """Update tenant by ID (admin access only)"""
    updated_tenant = await tenant_service.update_tenant_by_id(db, tenant_id, tenant_data)
    return ResponseFactory.transform_and_respond(updated_tenant, TenantResponse)


@routes.delete("/")
async def delete_tenant(
    tenant_id: UUID = Query(..., description="Tenant ID to delete"),
    _admin = Depends(get_current_admin),
    _authorized: bool = Depends(require_permission('tenant', 'delete')),
    db=Depends(get_default_db_session),
):
    """Delete tenant (admin access only)"""
    await tenant_service.delete_tenant_by_id(db, tenant_id)
    return ResponseFactory.deleted()


@routes.delete("/{tenant_id}")
async def delete_tenant_by_id(
        tenant_id: UUID,
        _admin = Depends(get_current_admin),
        _authorized: bool = Depends(require_permission('tenant', 'delete')),
        db=Depends(get_default_db_session),
):
    """Delete tenant by ID (admin access only)"""
    await tenant_service.delete_tenant_by_id(db, tenant_id)
    return ResponseFactory.deleted()
