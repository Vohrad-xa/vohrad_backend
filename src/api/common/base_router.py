"""Base router class with common patterns and utilities."""

from api.common.context_dependencies import get_shared_context, get_tenant_context
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from security.jwt import AuthenticatedUser
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, Optional, Type, TypeVar
from uuid import UUID
from web import PaginationParams, PaginationUtil, ResponseFactory, pagination_params

T                  = TypeVar("T", bound=BaseModel)
CreateSchemaType   = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType   = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class BaseRouterMixin:
    """Base mixin for common router patterns."""

    @staticmethod
    def create_paginated_response(
        items: List[Any], total: int, pagination: PaginationParams, response_model: Type[ResponseSchemaType]
    ):
        """Create standardized paginated response."""
        item_responses   = [response_model.model_validate(item) for item in items]
        paginated_result = PaginationUtil.paginate_query_result(item_responses, total, pagination.page, pagination.size)
        return ResponseFactory.paginated(paginated_result)

    @staticmethod
    def create_success_response(data: Any, response_model: Type[ResponseSchemaType], response_type: str = "success"):
        """Create standardized success response."""
        return ResponseFactory.transform_and_respond(data, response_model, response_type)

    @staticmethod
    def create_deleted_response(message: Optional[str] = None):
        """Create standardized deleted response."""
        return ResponseFactory.deleted(message)


class TenantScopedRouterMixin(BaseRouterMixin):
    """Mixin for tenant-scoped router patterns."""

    @staticmethod
    def get_tenant_context_dependency():
        """Get tenant context dependency."""
        return Depends(get_tenant_context)

    @staticmethod
    def extract_context(context) -> tuple[AuthenticatedUser, Any, AsyncSession]:
        """Extract user, tenant, and db from tenant context."""
        current_user, tenant, db = context
        return current_user, tenant, db


class SharedScopedRouterMixin(BaseRouterMixin):
    """Mixin for shared/admin-scoped router patterns."""

    @staticmethod
    def get_shared_context_dependency():
        """Get shared context dependency."""
        return Depends(get_shared_context)

    @staticmethod
    def extract_context(context) -> tuple[AuthenticatedUser, Any, AsyncSession]:
        """Extract user, tenant, and db from shared context."""
        current_user, tenant, db = context
        return current_user, tenant, db


class StandardRouterPatterns:
    """Common router endpoint patterns."""

    @staticmethod
    def create_list_endpoint(
        router            : APIRouter,
        service           : Any,
        response_model    : Type[ResponseSchemaType],
        context_dependency: Any,
        path              : str = "/",
        summary           : Optional[str] = None,
    ):
        """Create standardized GET list endpoint with pagination."""

        @router.get(path, summary=summary or "List items")
        async def list_items(pagination: PaginationParams = Depends(pagination_params), context=context_dependency):
            tenant, db = context
            items, total = await service.get_paginated(db, pagination.page, pagination.size, tenant)
            return BaseRouterMixin.create_paginated_response(items, total, pagination, response_model)

        return list_items

    @staticmethod
    def create_get_endpoint(
        router            : APIRouter,
        service           : Any,
        response_model    : Type[ResponseSchemaType],
        context_dependency: Any,
        path              : str = "/{item_id}",
        summary           : Optional[str] = None,
    ):
        """Create standardized GET single item endpoint."""

        @router.get(path, summary=summary or "Get item by ID")
        async def get_item(item_id: UUID, context=context_dependency):
            tenant, db = context
            item = await service.get_by_id(db, item_id, tenant)
            return BaseRouterMixin.create_success_response(item, response_model)

        return get_item

    @staticmethod
    def create_create_endpoint(
        router            : APIRouter,
        service           : Any,
        create_model      : Type[CreateSchemaType],
        response_model    : Type[ResponseSchemaType],
        context_dependency: Any,
        path              : str = "/",
        summary           : Optional[str] = None,
    ):
        """Create standardized POST create endpoint."""

        @router.post(path, status_code=status.HTTP_201_CREATED, summary=summary or "Create item")
        async def create_item(data: CreateSchemaType, context=context_dependency):
            tenant, db = context
            item = await service.create(db, data, tenant)
            return BaseRouterMixin.create_success_response(item, response_model, "created")

        return create_item

    @staticmethod
    def create_update_endpoint(
        router            : APIRouter,
        service           : Any,
        update_model      : Type[UpdateSchemaType],
        response_model    : Type[ResponseSchemaType],
        context_dependency: Any,
        path              : str = "/{item_id}",
        summary           : Optional[str] = None,
    ):
        """Create standardized PUT update endpoint."""

        @router.put(path, summary=summary or "Update item")
        async def update_item(item_id: UUID, data: UpdateSchemaType, context=context_dependency):
            tenant, db = context
            item = await service.update(db, item_id, data, tenant)
            return BaseRouterMixin.create_success_response(item, response_model)

        return update_item

    @staticmethod
    def create_delete_endpoint(
        router: APIRouter, service: Any, context_dependency: Any, path: str = "/{item_id}", summary: Optional[str] = None
    ):
        """Create standardized DELETE endpoint."""

        @router.delete(path, summary=summary or "Delete item")
        async def delete_item(item_id: UUID, context=context_dependency):
            tenant, db = context
            await service.delete(db, item_id, tenant)
            return BaseRouterMixin.create_deleted_response()

        return delete_item

    @staticmethod
    def create_search_endpoint(
        router            : APIRouter,
        service           : Any,
        response_model    : Type[ResponseSchemaType],
        context_dependency: Any,
        path              : str = "/search",
        summary           : Optional[str] = None,
    ):
        """Create standardized search endpoint with pagination."""

        @router.get(path, summary=summary or "Search items")
        async def search_items(
            q: str = Query(..., min_length=2, description="Search term"),
            pagination: PaginationParams = Depends(pagination_params),
            context=context_dependency,
        ):
            tenant, db = context
            items, total = await service.search(db, q, pagination.page, pagination.size, tenant)
            return BaseRouterMixin.create_paginated_response(items, total, pagination, response_model)

        return search_items
