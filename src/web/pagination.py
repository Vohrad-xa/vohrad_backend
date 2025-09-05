from constants import PaginationDefaults
from fastapi import Query
import math
from pydantic import BaseModel, Field
from typing import Generic, List, TypeVar

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for API requests"""

    page: int = Field(
        PaginationDefaults.DEFAULT_PAGE, ge=PaginationDefaults.DEFAULT_PAGE, description="Page number starting from 1"
    )
    size: int = Field(
        PaginationDefaults.DEFAULT_PAGE_SIZE,
        ge=PaginationDefaults.MIN_PAGE_SIZE,
        le=PaginationDefaults.MAX_PAGE_SIZE,
        description="Number of items per page",
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    items: List[T] = Field(description="List of items for current page")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    size: int = Field(description="Number of items per page")
    total_pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")


class PaginationUtil:
    """Utility class for handling pagination logic"""
    @staticmethod
    def paginate_query_result(items: List[T], total: int, page: int, size: int) -> PaginatedResponse[T]:
        total_pages = math.ceil(total / size) if total > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
        )

    @staticmethod
    def get_offset(page: int, size: int) -> int:
        """Calculate database offset for pagination"""
        return (page - 1) * size


def pagination_params(
    page: int = Query(
        PaginationDefaults.DEFAULT_PAGE, ge=PaginationDefaults.DEFAULT_PAGE, description="Page number starting from 1"
    ),
    size: int = Query(
        PaginationDefaults.DEFAULT_PAGE_SIZE,
        ge=PaginationDefaults.MIN_PAGE_SIZE,
        le=PaginationDefaults.MAX_PAGE_SIZE,
        description="Number of items per page",
    ),
) -> PaginationParams:
    return PaginationParams(page=page, size=size)
