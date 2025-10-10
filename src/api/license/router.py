"""License routes for tenant users."""

from .schema import LicenseResponse
from .service import license_service
from api.common import BaseRouterMixin
from api.common.context_dependencies import get_shared_context_no_license_check
from fastapi import APIRouter, Depends
from web import PaginatedResponse, PaginationParams, SuccessResponse, pagination_params

routes = APIRouter(
    tags   = ["licenses"],
    prefix = "/licenses",
)


@routes.get("/", response_model=SuccessResponse[PaginatedResponse[LicenseResponse]])
async def list_tenant_licenses(
    pagination: PaginationParams = Depends(pagination_params),
    context = Depends(get_shared_context_no_license_check),
):
    """List all licenses for the current tenant (no license validation required)."""
    _current_user, tenant, db = context
    licenses, total = await license_service.get_multi(
        db,
        pagination.page,
        pagination.size,
        tenant_id = tenant.tenant_id
    )
    return BaseRouterMixin.create_paginated_response(
        licenses,
        total,
        pagination,
        LicenseResponse
    )
