"""Reusable base schema classes for consistent model patterns."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID


class BaseCreateSchema(BaseModel):
    """Base schema for create operations - extend for new models."""

    pass


class BaseUpdateSchema(BaseModel):
    """Base schema for update operations - extend for new models."""

    pass


class BaseResponseSchema(BaseModel):
    """Base schema for response operations - common fields for all entities."""

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standardized error response schema - reusable across all APIs."""

    detail      : str
    error_code  : Optional[str] = None
    field_errors: Optional[dict] = None


class PaginatedResponseMeta(BaseModel):
    """Pagination metadata for consistent paginated responses."""

    page        : int
    size        : int
    total       : int
    total_pages : int
    has_next    : bool
    has_previous: bool


class TenantScopedSchema(BaseModel):
    """Base schema for tenant-scoped entities."""

    tenant_id: Optional[UUID] = None
