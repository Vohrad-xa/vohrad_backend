from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_authenticated_context, get_shared_context
from api.tenant.schema import TenantCreate, TenantResponse, TenantUpdate
from api.tenant.service import tenant_service
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
        context=Depends(get_shared_context),
):
    """Create a new tenant (admin access only)"""
    _current_user, _current_tenant, db = context
    tenant = await tenant_service.create_tenant(db, tenant_data)
    return ResponseFactory.transform_and_respond(tenant, TenantResponse, "created")


@routes.get("/search")
async def search_tenants(
        q: str = Query(..., min_length=2, description="Search term"),
        pagination: PaginationParams = Depends(pagination_params),
        context=Depends(get_shared_context),
):
    """Search tenants by email, city, or industry (admin access only)"""
    _current_user, _current_tenant, db = context
    tenants, total = await tenant_service.search(db, q, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(tenants, total, pagination, TenantResponse)


@routes.get("/list")
async def get_tenants(
        pagination: PaginationParams = Depends(pagination_params),
        context=Depends(get_shared_context),
):
    """Get a paginated list of tenants (admin access only)"""
    _current_user, _current_tenant, db = context
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
        context=Depends(get_shared_context),
):
    """Get tenant by ID (admin access only)"""
    _current_user, _current_tenant, db = context
    tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
    return ResponseFactory.transform_and_respond(tenant, TenantResponse)


@routes.put("/")
async def update_tenant(
        tenant_data: TenantUpdate,
        context=Depends(get_shared_context),
):
    """Update tenant"""
    _current_user, tenant, db = context
    updated_tenant = await tenant_service.update_tenant(db, tenant, tenant_data)
    return ResponseFactory.transform_and_respond(updated_tenant, TenantResponse)


@routes.put("/{tenant_id}")
async def update_tenant_by_id(
        tenant_id: UUID,
        tenant_data: TenantUpdate,
        context=Depends(get_shared_context),
):
    """Update tenant by ID (admin access only)"""
    _current_user, _current_tenant, db = context
    updated_tenant = await tenant_service.update_tenant_by_id(db, tenant_id, tenant_data)
    return ResponseFactory.transform_and_respond(updated_tenant, TenantResponse)


@routes.delete("/")
async def delete_tenant(context=Depends(get_shared_context)):
    """Delete tenant"""
    _current_user, tenant, db = context
    await tenant_service.delete_tenant(db, tenant)
    return ResponseFactory.deleted()


@routes.delete("/{tenant_id}")
async def delete_tenant_by_id(
        tenant_id: UUID,
        context=Depends(get_shared_context),
):
    """Delete tenant by ID (admin access only)"""
    _current_user, _current_tenant, db = context
    await tenant_service.delete_tenant_by_id(db, tenant_id)
    return ResponseFactory.deleted()
