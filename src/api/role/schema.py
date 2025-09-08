"""Role management schemas following project patterns."""

from api.common import BaseCreateSchema, BaseResponseSchema, BaseUpdateSchema
from constants import RoleScope, RoleStage, RoleType, ValidationConstraints, ValidationMessages
from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID


class RoleCreate(BaseCreateSchema):
    """Schema for creating role."""

    name       : str
    description: Optional[str] = None
    role_type  : Optional[RoleType]  = RoleType.PREDEFINED
    role_scope : Optional[RoleScope] = RoleScope.TENANT
    stage      : Optional[RoleStage] = RoleStage.GA

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate role name."""
        if not v or not v.strip():
            raise ValueError(ValidationMessages.ROLE_NAME_REQUIRED)
        if len(v.strip()) < ValidationConstraints.MIN_ROLE_LENGTH:
            raise ValueError(ValidationMessages.ROLE_TOO_SHORT)
        if len(v.strip()) > ValidationConstraints.MAX_ROLE_LENGTH:
            raise ValueError(ValidationMessages.ROLE_TOO_LONG)
        from security.policy import is_reserved_role

        if is_reserved_role(v):
            raise ValueError(f"Role name '{v}' is reserved for system roles")

        return v.strip().lower()

    @field_validator("role_type")
    @classmethod
    def validate_role_type(cls, v):
        """Only PREDEFINED roles can be created via API."""
        if v == RoleType.BASIC:
            raise ValueError("Basic roles can only be created by system administrators")
        return v

    @field_validator("role_scope")
    @classmethod
    def validate_role_scope(cls, v, info):
        """Basic roles must be global scope only."""
        role_type = info.data.get("role_type") if hasattr(info, "data") and info.data else None

        if role_type == RoleType.BASIC and v != RoleScope.GLOBAL:
            raise ValueError("Basic roles can only have global scope")

        return v

    @field_validator("stage")
    @classmethod
    def validate_stage_for_role_type(cls, v, info):
        """Enforce that BASIC/PREDEFINED roles are always GA."""
        role_type = info.data.get("role_type") if hasattr(info, "data") and info.data else None
        if role_type in (RoleType.BASIC, RoleType.PREDEFINED):
            if v is None:
                return RoleStage.GA
            if v != RoleStage.GA:
                raise ValueError("BASIC/PREDEFINED roles must have stage GA")
        return v


class RoleUpdate(BaseUpdateSchema):
    """Schema for updating role - all fields optional."""

    name       : Optional[str]  = None
    description: Optional[str]  = None
    is_active  : Optional[bool]      = None
    stage      : Optional[RoleStage] = None
    etag       : Optional[str]  = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate role name if provided - consistent validation."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError(ValidationMessages.ROLE_NAME_REQUIRED)
            if len(v.strip()) < ValidationConstraints.MIN_ROLE_LENGTH:
                raise ValueError(ValidationMessages.ROLE_TOO_SHORT)
            if len(v.strip()) > ValidationConstraints.MAX_ROLE_LENGTH:
                raise ValueError(ValidationMessages.ROLE_TOO_LONG)
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
    stage              : RoleStage
    is_mutable         : bool
    permissions_mutable: bool
    managed_by         : Optional[str] = None
    is_deletable       : bool
    tenant_id          : Optional[UUID] = None
    etag               : str


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
