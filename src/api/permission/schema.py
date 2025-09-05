"""Permission schemas following enterprise patterns."""

from api.common import BaseCreateSchema, BaseResponseSchema, BaseUpdateSchema
from constants import ValidationMessages
from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID


class PermissionCreate(BaseCreateSchema):
    """Schema for creating permission"""
    role_id : UUID
    resource: str
    action  : str

    @field_validator("resource")
    @classmethod
    def validate_resource(cls, v):
        if not v or not v.strip():
            raise ValueError(ValidationMessages.RESOURCE_REQUIRED)
        return v.strip().lower()

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if not v or not v.strip():
            raise ValueError(ValidationMessages.ACTION_REQUIRED)
        return v.strip().lower()


class PermissionUpdate(BaseUpdateSchema):
    """Schema for updating permission"""
    role_id : Optional[UUID] = None
    resource: Optional[str]  = None
    action  : Optional[str]  = None

    @field_validator("resource")
    @classmethod
    def validate_resource(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError(ValidationMessages.RESOURCE_REQUIRED)
            return v.strip().lower()
        return v

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError(ValidationMessages.ACTION_REQUIRED)
            return v.strip().lower()
        return v


class PermissionResponse(BaseResponseSchema):
    """Schema for permission response"""
    role_id : UUID
    resource: str
    action  : str


class PermissionListMeta(BaseModel):
    """Metadata for permission list responses - consistent with pagination patterns."""

    total       : int
    page        : int
    size        : int
    total_pages : int
    has_next    : bool
    has_previous: bool


class PermissionListResponse(BaseModel):
    """Response schema for permission list operations."""

    permissions: list[PermissionResponse]
    meta       : PermissionListMeta
