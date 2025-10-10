"""License routes for tenant users."""

from .schema import LicenseResponse
from .service import license_service
from api.common import BaseRouterMixin
from api.common.context_dependencies import get_shared_context_no_license_check
from api.stripe import stripe_payment_service
from config import get_settings
from exceptions import ExceptionFactory
from fastapi import APIRouter, Depends
from web import PaginatedResponse, PaginationParams, ResponseFactory, SuccessResponse, pagination_params

routes = APIRouter(
    tags   = ["licenses"],
    prefix = "/licenses",
)


@routes.get(
    "/",
    response_model = SuccessResponse[PaginatedResponse[LicenseResponse]]
)
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


@routes.post(
    "/renew",
    response_model = SuccessResponse[dict]
)
async def renew_current_license(
    context = Depends(get_shared_context_no_license_check),
):
    """Create or reuse a renewal invoice for the tenant's current license."""
    _current_user, tenant, db = context

    if not tenant.license_id:
        raise ExceptionFactory.business_rule(
            "Tenant does not have a license assigned",
            {"tenant_id": str(tenant.tenant_id)},
        )

    settings = get_settings()
    result: dict = await stripe_payment_service.process_invoice_flow(
        db,
        tenant.license_id,
        extension_days=settings.LICENSE_TERM_DAYS_DEFAULT,
    )

    return ResponseFactory.success(result)
