"""Tenant router."""

from api.common.context_dependencies import (
    get_authenticated_context_no_license_check,
    get_shared_context,
    get_shared_context_no_license_check,
)
from api.permission.dependencies import RequireTenantManagement
from api.tenant.schema import TenantResponse, TenantSettingsUpdate, TenantUpdate
from api.tenant.service import tenant_service
from fastapi import APIRouter, Depends
from web import (
    ResponseFactory,
    SuccessResponse,
    UpdatedResponse,
)

routes = APIRouter(
    tags   = ["tenant"],
    prefix = "/tenant",
)


@routes.get("/", response_model=SuccessResponse[TenantResponse])
async def get_current_tenant_endpoint(context=Depends(get_authenticated_context_no_license_check)):
    """Get the current tenant (no active license required)"""
    _user, tenant = context
    return ResponseFactory.success(tenant, response_model=TenantResponse)


@routes.put("/settings", response_model=UpdatedResponse[TenantResponse])
async def update_tenant_settings(
    settings: TenantSettingsUpdate,
    context = Depends(get_shared_context),
    _authorized: bool = Depends(RequireTenantManagement),
):
    """Allow tenant managers to update timezone and working hours for their own tenant."""
    _current_user, tenant, db = context

    data   = settings.model_dump(exclude_unset=True)
    update = TenantUpdate(**data)

    updated = await tenant_service.update_tenant(db, tenant, update)
    return ResponseFactory.updated(updated, response_model=TenantResponse)


@routes.get("/license-info", response_model=SuccessResponse[dict])
async def get_current_tenant_license_info(context=Depends(get_shared_context_no_license_check)):
    """Get current tenant's license information including seat usage (no active license required)."""
    _current_user, tenant, db = context

    from api.license.service import license_service

    license_info: dict = await license_service.get_tenant_license_info(db, tenant)
    return ResponseFactory.success(license_info)
