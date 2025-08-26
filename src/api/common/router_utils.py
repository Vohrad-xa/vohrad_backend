"""Common router utilities for consistent endpoint patterns across all models."""

from api.common.dependencies import get_current_tenant
from database import get_tenant_db_session
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from typing import List
from typing import Type
from typing import TypeVar
from uuid import UUID
from web import PaginationParams
from web import PaginationUtil
from web import ResponseFactory
from web import pagination_params

T = TypeVar("T")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)

class CRUDRouterFactory:
    """Factory for creating standardized CRUD routes for any model."""

    @staticmethod

    def create_crud_router(
        service: Any,
        create_schema: Type[CreateSchemaType],
        update_schema: Type[UpdateSchemaType],
        response_schema: Type[ResponseSchemaType],
        route_prefix: str,
        tags: List[str],
        tenant_scoped: bool = True,
    ) -> APIRouter:
        """Create a standardized CRUD router for any model.

        Args:
            service: Service instance with CRUD methods
            create_schema: Pydantic schema for creation
            update_schema: Pydantic schema for updates
            response_schema: Pydantic schema for responses
            route_prefix: URL prefix for routes (e.g., '/users')
            tags: OpenAPI tags for documentation
            tenant_scoped: Whether routes are tenant-scoped

        Returns:
            APIRouter with standard CRUD endpoints
        """
        router = APIRouter(prefix=route_prefix, tags=tags)

        # Dependencies based on tenant scoping
        if tenant_scoped:
            db_dep = get_tenant_db_session
            tenant_dep = get_current_tenant
        else:
            # For non-tenant-scoped resources, use different dependencies
            db_dep = get_tenant_db_session  # a different one for admin routes
            tenant_dep = None

        # CREATE endpoint
        @router.post("/", status_code=status.HTTP_201_CREATED)
        async def create_resource(
            data: CreateSchemaType,
            tenant=Depends(tenant_dep) if tenant_dep else None,
            db: AsyncSession = Depends(db_dep),
        ):
            """Create new resource"""
            if tenant:
                resource = await service.create(db, data, tenant)
            else:
                resource = await service.create(db, data)
            return ResponseFactory.transform_and_respond(resource, response_schema, "created")

        # READ ALL endpoint (with pagination)
        @router.get("/")
        async def list_resources(
            pagination: PaginationParams = Depends(pagination_params),
            tenant=Depends(tenant_dep) if tenant_dep else None,
            db: AsyncSession = Depends(db_dep),
        ):
            """Get paginated list of resources"""
            if tenant:
                resources, total = await service.get_paginated(db, pagination.page, pagination.size, tenant)
            else:
                resources, total = await service.get_paginated(db, pagination.page, pagination.size)

            resource_responses = [response_schema.model_validate(resource) for resource in resources]
            paginated_result = PaginationUtil.paginate_query_result(
                resource_responses, total, pagination.page, pagination.size
            )
            return ResponseFactory.paginated(paginated_result)

        # READ ONE endpoint
        @router.get("/{resource_id}")
        async def get_resource(
            resource_id: UUID, tenant=Depends(tenant_dep) if tenant_dep else None, db: AsyncSession = Depends(db_dep)
        ):
            """Get resource by ID"""
            if tenant:
                resource = await service.get_by_id(db, resource_id, tenant)
            else:
                resource = await service.get_by_id(db, resource_id)
            return ResponseFactory.transform_and_respond(resource, response_schema)

        # UPDATE endpoint
        @router.put("/{resource_id}")
        async def update_resource(
            resource_id: UUID,
            data: UpdateSchemaType,
            tenant=Depends(tenant_dep) if tenant_dep else None,
            db: AsyncSession = Depends(db_dep),
        ):
            """Update resource"""
            if tenant:
                resource = await service.update(db, resource_id, data, tenant)
            else:
                resource = await service.update(db, resource_id, data)
            return ResponseFactory.transform_and_respond(resource, response_schema)

        # DELETE endpoint
        @router.delete("/{resource_id}")
        async def delete_resource(
            resource_id: UUID, tenant=Depends(tenant_dep) if tenant_dep else None, db: AsyncSession = Depends(db_dep)
        ):
            """Delete resource"""
            if tenant:
                await service.delete(db, resource_id, tenant)
            else:
                await service.delete(db, resource_id)
            return ResponseFactory.deleted()

        return router

class SearchableRouterMixin:
    """Mixin to add search functionality to routers."""

    @staticmethod

    def add_search_route(
        router: APIRouter, service: Any, response_schema: Type[ResponseSchemaType], tenant_scoped: bool = True
    ):
        """Add search endpoint to existing router."""
        # Dependencies based on tenant scoping
        if tenant_scoped:
            db_dep = get_tenant_db_session
            tenant_dep = get_current_tenant
        else:
            db_dep = get_tenant_db_session
            tenant_dep = None

        @router.get("/search")
        async def search_resources(
            q: str = Query(..., min_length=2, description="Search term"),
            pagination: PaginationParams = Depends(pagination_params),
            tenant=Depends(tenant_dep) if tenant_dep else None,
            db: AsyncSession = Depends(db_dep),
        ):
            """Search resources"""
            if tenant:
                resources, total = await service.search(db, q, pagination.page, pagination.size, tenant)
            else:
                resources, total = await service.search(db, q, pagination.page, pagination.size)

            resource_responses = [response_schema.model_validate(resource) for resource in resources]
            paginated_result = PaginationUtil.paginate_query_result(
                resource_responses, total, pagination.page, pagination.size
            )
            return ResponseFactory.paginated(paginated_result)
