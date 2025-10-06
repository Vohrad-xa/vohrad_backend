"""Location schemas."""

from api.common.schemas import BaseResponseSchema
from decimal import Decimal
from pydantic import BaseModel, Field, computed_field, field_validator
from typing import Any, Optional
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


class ItemLocationData(BaseModel):
    """Item summary for location responses (includes quantity)."""

    id      : UUID
    name    : str
    code    : str
    quantity: Decimal


class LocationResponse(BaseResponseSchema):
    """Schema for location response."""

    id         : UUID
    name       : str
    code       : str
    parent_id  : Optional[UUID] = None
    path       : Optional[str]  = None
    description: Optional[str]  = None
    is_active  : bool


class LocationDetailResponse(LocationResponse):
    """Detailed location response with items (detail views only)."""

    item_locations: Optional[list[Any]] = Field(default=None, exclude=True)

    @computed_field  # type: ignore[misc]
    @property
    def items(self) -> Optional[list[ItemLocationData]]:
        """Derived items with quantities from item_locations relationship when loaded."""
        if not self.item_locations:
            return None

        return [
            ItemLocationData(
                id       = il.item.id,
                name     = il.item.name,
                code     = il.item.code,
                quantity = il.quantity,
            )
            for il in self.item_locations
            if il.item
        ] or None
