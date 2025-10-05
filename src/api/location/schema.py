"""Location schemas."""

from api.common.schemas import BaseResponseSchema
from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID


class LocationBase(BaseModel):
    """Base location schema."""

    name       : str
    code       : str
    parent_id  : Optional[UUID] = None
    description: Optional[str] = None
    is_active  : bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if not v:
            raise ValueError("Location name is required")
        if len(v) > 255:
            raise ValueError("Location name cannot exceed 255 characters")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if not v:
            raise ValueError("Location code is required")
        if len(v) > 50:
            raise ValueError("Location code cannot exceed 50 characters")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        if v and len(v) > 500:
            raise ValueError("Description cannot exceed 500 characters")
        return v


class LocationCreate(LocationBase):
    """Schema for creating location."""

    pass


class LocationUpdate(BaseModel):
    """Schema for updating location."""

    name       : Optional[str]  = None
    code       : Optional[str]  = None
    parent_id  : Optional[UUID] = None
    description: Optional[str]  = None
    is_active  : Optional[bool] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        if v is not None and len(v) > 255:
            raise ValueError("Location name cannot exceed 255 characters")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if v is not None and len(v) > 50:
            raise ValueError("Location code cannot exceed 50 characters")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        if v and len(v) > 500:
            raise ValueError("Description cannot exceed 500 characters")
        return v


class LocationResponse(BaseResponseSchema):
    """Schema for location response."""

    id         : UUID
    name       : str
    code       : str
    parent_id  : Optional[UUID] = None
    path       : Optional[str]  = None
    description: Optional[str]  = None
    is_active  : bool
