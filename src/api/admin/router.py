"""Admin routes with tenant context switching."""

from .dependencies import get_admin_params
from .schema import AdminResponse
from .service import admin_service
from api.common import BaseRouterMixin
from api.license import LicenseCreate, LicenseResponse, license_service
from api.permission import PermissionResponse, permission_service
from api.role import RoleResponse, role_service
from api.stripe import stripe_payment_service
from api.tenant import TenantResponse, TenantUpdate, tenant_service
from exceptions import ExceptionFactory
from fastapi import APIRouter, Depends, Query, status
from uuid import UUID
from web import (
    CreatedResponse,
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


@routes.get(
    "/users",
    response_model = SuccessResponse[PaginatedResponse[AdminResponse]]
)
async def list_admin_users(params = Depends(get_admin_params)):
    """List all admin users."""
    pagination, _user, db = params
    items, total = await admin_service.get_multi(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, AdminResponse)


@routes.get(
    "/tenants",
    response_model = SuccessResponse[PaginatedResponse[TenantResponse]]
)
async def list_all_tenants(params = Depends(get_admin_params)):
    """List all tenants."""
    pagination, _user, db = params
    items, total = await tenant_service.get_multi(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, TenantResponse)


@routes.get(
    "/roles",
    response_model = SuccessResponse[PaginatedResponse[RoleResponse]]
)
async def list_all_roles(params = Depends(get_admin_params)):
    """List all roles."""
    pagination, _user, db = params
    items, total = await role_service.get_multi(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, RoleResponse)


@routes.get(
    "/permissions",
    response_model = SuccessResponse[PaginatedResponse[PermissionResponse]]
)
async def list_all_permissions(params = Depends(get_admin_params)):
    """List all permissions."""
    pagination, _user, db = params
    items, total = await permission_service.get_multi(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, PermissionResponse)


@routes.put(
    "/tenants/{tenant_id}",
    response_model=UpdatedResponse[TenantResponse]
)
async def update_tenant(
    tenant_id  : UUID,
    tenant_data: TenantUpdate,
    params = Depends(get_admin_params)
) -> SuccessResponse[TenantResponse]:
    """Update tenant by ID (admin access only)."""
    _pagination, _user, db = params
    updated_tenant = await tenant_service.update_tenant_by_id(db, tenant_id, tenant_data)
    return ResponseFactory.updated(updated_tenant, response_model=TenantResponse)


@routes.delete(
    "/tenants/{tenant_id}",
    response_model = DeletedResponse
)
async def delete_tenant(
    tenant_id: UUID,
    params = Depends(get_admin_params)
) -> DeletedResponse:
    """Delete tenant."""
    _pagination, _user, db = params
    await tenant_service.delete_tenant_by_id(db, tenant_id)
    return ResponseFactory.deleted("tenant")


@routes.post(
    "/licenses",
    status_code    = status.HTTP_201_CREATED,
    response_model = CreatedResponse[LicenseResponse],
)
async def create_license(
    license_data: LicenseCreate,
    params=Depends(get_admin_params),
):
    """Create new license (admin only)."""
    _pagination, _user, db = params
    license_obj: LicenseResponse = await license_service.create_license(db, license_data)
    return ResponseFactory.created(license_obj, response_model=LicenseResponse)


@routes.get(
    "/licenses",
    response_model = SuccessResponse[PaginatedResponse[LicenseResponse]]
)
async def list_all_licenses(params=Depends(get_admin_params)):
    """List all licenses (admin only)."""
    pagination, _user, db = params
    items, total = await license_service.get_multi(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(items, total, pagination, LicenseResponse)


@routes.put(
    "/tenants/{tenant_id}/license",
    response_model = UpdatedResponse[TenantResponse]
)
async def assign_tenant_license(
    tenant_id : UUID,
    license_id: UUID = Query(..., description="License ID to assign to tenant"),
    params = Depends(get_admin_params),
):
    """Assign/update license for a tenant (admin only)."""
    _pagination, _user, db = params
    await license_service.activate_license(db, license_id)
    updated_tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
    return ResponseFactory.updated(updated_tenant, response_model=TenantResponse)


@routes.post(
    "/tenants/{tenant_id}/license/activate",
    response_model = UpdatedResponse[TenantResponse]
)
async def activate_tenant_license(
    tenant_id: UUID,
    params = Depends(get_admin_params),
):
    """Activate tenant's current license (admin only)."""
    _pagination, _user, db = params
    tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
    if not tenant.license_id:
        raise ExceptionFactory.business_rule("Tenant does not have a license assigned", {"tenant_id": str(tenant_id)})
    await license_service.activate_license(db, tenant.license_id)
    updated_tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
    return ResponseFactory.updated(updated_tenant, response_model=TenantResponse)


@routes.post(
    "/tenants/{tenant_id}/license/suspend",
    response_model = UpdatedResponse[TenantResponse]
)
async def suspend_tenant_license(
    tenant_id: UUID,
    params=Depends(get_admin_params),
):
    """Suspend tenant's license (admin only)."""
    _pagination, _user, db = params
    tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
    if not tenant.license_id:
        raise ExceptionFactory.business_rule("Tenant does not have a license assigned", {"tenant_id": str(tenant_id)})
    await license_service.suspend_license(db, tenant.license_id)
    updated_tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
    return ResponseFactory.updated(updated_tenant, response_model=TenantResponse)


@routes.get(
    "/tenants/{tenant_id}/license-info",
    response_model = SuccessResponse[dict]
)
async def get_tenant_license_info(
    tenant_id: UUID,
    params=Depends(get_admin_params),
):
    """Get license information for a tenant including seat usage (admin only)."""
    _pagination, _user, db = params
    tenant = await tenant_service.get_tenant_by_id(db, tenant_id)
    license_info: dict = await license_service.get_tenant_license_info(db, tenant)
    return ResponseFactory.success(license_info)


@routes.post(
    "/licenses/{license_id}/invoice",
    response_model = SuccessResponse[dict]
)
async def create_license_invoice(
    license_id: UUID,
    params=Depends(get_admin_params),
):
    """Create and send Stripe invoice for license (admin only)."""
    _pagination, _user, db = params

    result: dict = await stripe_payment_service.process_invoice_flow(db, license_id)

    if result["code"] == "already_active":
        return ResponseFactory.success(result["payload"])

    if result["code"] == "activated":
        return ResponseFactory.success(result["payload"])

    if result["code"] == "invoice_pending":
        return ResponseFactory.success(result["payload"])

    return ResponseFactory.success(result["payload"])
