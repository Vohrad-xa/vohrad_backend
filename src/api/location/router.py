"""Location router."""

from api.common.base_router import BaseRouterMixin
from api.common.context_dependencies import get_tenant_context
from api.location.schema import LocationCreate, LocationResponse
from api.location.service import location_service
from fastapi import APIRouter, Depends, status
from web import (
    CreatedResponse,
    PaginatedResponse,
    PaginationParams,
    ResponseFactory,
    SuccessResponse,
    pagination_params,
)

routes = APIRouter(
    tags   = ["locations"],
    prefix = "/locations",
)


@routes.post(
    "/",
    status_code    = status.HTTP_201_CREATED,
    response_model = CreatedResponse[LocationResponse]
)
async def create_location(
    location_data: LocationCreate,
    context=Depends(get_tenant_context),
):
    """Create new location"""
    _, _, db = context
    location = await location_service.create_location(db, location_data)
    return ResponseFactory.created(location)


@routes.get("/", response_model=SuccessResponse[PaginatedResponse[LocationResponse]])
async def get_locations(
    pagination: PaginationParams = Depends(pagination_params),
    context=Depends(get_tenant_context),
):
    """Get paginated list of locations"""
    _, _, db = context
    locations, total = await location_service.get_locations_paginated(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(locations, total, pagination, LocationResponse)
