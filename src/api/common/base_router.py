"""Base router utilities for common patterns."""

from pydantic import BaseModel
from typing import Any, List, Type, TypeVar
from web import PaginationParams, PaginationUtil, ResponseFactory

ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class BaseRouterMixin:
    """Base mixin for pagination patterns."""

    @staticmethod
    def create_paginated_response(
        items: List[Any],
        total: int,
        pagination: PaginationParams,
        response_model: Type[ResponseSchemaType]
    ):
        """Create standardized paginated response with smart messaging."""
        item_responses = [response_model.model_validate(item) for item in items]
        paginated_result = PaginationUtil.paginate_query_result(
            item_responses, total, pagination.page, pagination.size
        )
        return ResponseFactory.success(paginated_result, response_model=response_model)
