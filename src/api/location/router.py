"""Location router."""

from .schema import LocationCreate, LocationDetailResponse, LocationResponse, LocationUpdate
from .service import location_service
from api.common import BaseRouterMixin
from api.common.context_dependencies import get_tenant_context
from api.permission.dependencies import RequireLocationCreate, RequireLocationDelete, RequireLocationUpdate
from fastapi import APIRouter, Depends, Query, status
from uuid import UUID
from web import (
    CreatedResponse,
    DeletedResponse,
    PaginatedResponse,
    PaginationParams,
    ResponseFactory,
    SuccessResponse,
    UpdatedResponse,
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
    _authorized: bool = Depends(RequireLocationCreate),
):
    """Create new location"""
    _, _, db = context
    location = await location_service.create_location(db, location_data)
    return ResponseFactory.created(location)


@routes.get("/", response_model=SuccessResponse[PaginatedResponse[LocationResponse]])
async def get_locations(
    pagination: PaginationParams = Depends(pagination_params),
    odata_filter: str | None = Query(None, description="OData filter expression"),
    context=Depends(get_tenant_context),
):
    """Get paginated list of locations with optional OData filtering"""
    _, _, db = context

    if odata_filter:
        locations, total = await location_service.get_locations_with_filter(db, odata_filter, pagination.page, pagination.size)
    else:
        locations, total = await location_service.get_locations(db, pagination.page, pagination.size)
    return BaseRouterMixin.create_paginated_response(locations, total, pagination, LocationResponse)


@routes.get("/{location_id}", response_model=SuccessResponse[LocationDetailResponse])
async def get_location_detail(
    location_id: UUID,
    context=Depends(get_tenant_context),
):
    """Get location details with all items in that location"""
    _, _, db = context
    location = await location_service.get_location_by_id(db, location_id)
    return ResponseFactory.success(location, response_model=LocationDetailResponse)


@routes.put("/{location_id}", response_model=UpdatedResponse[LocationResponse])
async def update_location(
    location_id  : UUID,
    location_data: LocationUpdate,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireLocationUpdate),
):
    """Update location"""
    _, _, db = context
    location = await location_service.update_location(db, location_id, location_data)
    return ResponseFactory.updated(location, response_model=LocationResponse)


@routes.delete("/{location_id}", response_model=DeletedResponse)
async def delete_location(
    location_id: UUID,
    context=Depends(get_tenant_context),
    _authorized: bool = Depends(RequireLocationDelete),
):
    """Delete location (only if it has no items and no children)"""
    _, _, db = context
    await location_service.delete_location(db, location_id)
    return ResponseFactory.deleted("location")
