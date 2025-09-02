"""Role management schemas following project patterns."""

from api.common import BaseCreateSchema
from api.common import BaseResponseSchema
from api.common import BaseUpdateSchema
from constants.enums import RoleScope
from constants.enums import RoleType
from pydantic import BaseModel
from pydantic import field_validator
from typing import Optional
from uuid import UUID


class RoleCreate(BaseCreateSchema):
    """Schema for creating role."""

    name       : str
    description: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate role name."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        if len(v.strip()) < 2:
            raise ValueError("name must be at least 2 characters")
        if len(v.strip()) > 50:
            raise ValueError("name cannot exceed 50 characters")
        return v.strip().lower()


class RoleUpdate(BaseUpdateSchema):
    """Schema for updating role - all fields optional."""

    name       : Optional[str] = None
    description: Optional[str] = None
    is_active  : Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate role name if provided - consistent validation."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("name cannot be empty")
            if len(v.strip()) < 2:
                raise ValueError("name must be at least 2 characters")
            if len(v.strip()) > 50:
                raise ValueError("name cannot exceed 50 characters")
            return v.strip().lower()
        return v


class RoleResponse(BaseResponseSchema):
    """Schema for role response - follows project patterns."""

    id                 : UUID
    name               : str
    description        : Optional[str] = None
    is_active          : bool
    role_type          : RoleType
    role_scope         : RoleScope
    is_mutable         : bool
    permissions_mutable: bool
    managed_by         : Optional[str] = None
    is_deletable       : bool
    tenant_id          : Optional[UUID] = None


class RoleListMeta(BaseModel):
    """Metadata for role list responses - consistent with pagination patterns."""

    total       : int
    page        : int
    size        : int
    total_pages : int
    has_next    : bool
    has_previous: bool


class RoleListResponse(BaseModel):
    """Response schema for role list operations."""

    roles: list[RoleResponse]
    meta : RoleListMeta
